// Cut the subject off its background with Apple Vision. usage: swift matte.swift in.png out.png
import AppKit
import CoreImage
import Vision

let a = CommandLine.arguments
let input = CIImage(contentsOf: URL(fileURLWithPath: a[1]))!
let handler = VNImageRequestHandler(ciImage: input)
let req = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([req])
guard let obs = req.results?.first else { fatalError("no subject found in \(a[1])") }
let buf = try obs.generateMaskedImage(ofInstances: obs.allInstances, from: handler, croppedToInstancesExtent: false)
let ctx = CIContext()
try ctx.writePNGRepresentation(of: CIImage(cvPixelBuffer: buf), to: URL(fileURLWithPath: a[2]),
                               format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
print("wrote \(a[2])")
