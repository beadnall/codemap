import AppKit
import WebKit

// Renders an HTML file in an offscreen WKWebView and writes a PNG. This runs
// the page's JavaScript, which is the whole point: static analysis proves a
// script parses, not that it draws anything.
let args = CommandLine.arguments
guard args.count == 5 else { exit(2) }
let page = URL(fileURLWithPath: args[1])
let out  = URL(fileURLWithPath: args[2])
let w = Double(args[3])!, h = Double(args[4])!

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

let frame = NSRect(x: 0, y: 0, width: w, height: h)
let window = NSWindow(contentRect: frame, styleMask: [.borderless],
                      backing: .buffered, defer: false)
let web = WKWebView(frame: frame, configuration: WKWebViewConfiguration())
window.contentView = web
window.orderBack(nil)

final class Done: NSObject, WKNavigationDelegate {
    func webView(_ web: WKWebView, didFinish nav: WKNavigation!) {
        // Two seconds: the layout settles, the flow animation starts, and the
        // dots move off their starting positions so the render shows motion.
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            let cfg = WKSnapshotConfiguration()
            cfg.rect = web.bounds
            web.takeSnapshot(with: cfg) { image, error in
                guard let image,
                      let tiff = image.tiffRepresentation,
                      let rep = NSBitmapImageRep(data: tiff),
                      let png = rep.representation(using: .png, properties: [:]) else {
                    FileHandle.standardError.write("snapshot failed: \(error?.localizedDescription ?? "nil")\n".data(using: .utf8)!)
                    exit(1)
                }
                try? png.write(to: out)
                print("wrote \(out.lastPathComponent)")
                exit(0)
            }
        }
    }
}
let done = Done()
web.navigationDelegate = done
// loadHTMLString, not loadFileURL: WKWebView assumes Latin-1 for a file://
// document with no charset in its head, and the artifact wrapper supplies that
// head, not us. Em dashes rendered as "a€" until this changed.
let html = try! String(contentsOf: page, encoding: .utf8)
web.loadHTMLString(html, baseURL: page.deletingLastPathComponent())
DispatchQueue.main.asyncAfter(deadline: .now() + 25) { exit(3) }
app.run()
