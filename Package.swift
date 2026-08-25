// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "LibDovi",
    platforms: [
        // IPTVX keeps its OS 15 app baseline and only exposes Aether playback from OS 17.
        .iOS(.v15),
        .tvOS(.v15),
        .macOS(.v14),
        .visionOS(.v1),
    ],
    products: [
        .library(
            name: "Dovi",
            targets: ["Dovi"]
        ),
    ],
    targets: [
        .binaryTarget(
            name: "Dovi",
            path: "Dovi.xcframework"
        ),
    ]
)
