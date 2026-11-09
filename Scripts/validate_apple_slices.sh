#!/bin/bash
# Run through a FlowDeck aggregate target; links each slice at the consumer OS floor.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
output="${LIBDOVI_VALIDATION_OUTPUT:-${TMPDIR:-/tmp}/libdovi-validation-links}"
mkdir -p "$output"
while read -r slice arch sdk target; do
    xcrun --sdk "$sdk" clang -target "$target" -isysroot "$(xcrun --sdk "$sdk" --show-sdk-path)" \
        -I "$root/Dovi.xcframework/$slice/Headers" "$root/Tests/PolynomialMappingTests.c" \
        "$root/Dovi.xcframework/$slice/libdovi.a" -o "$output/$target" \
        -framework Security -framework CoreFoundation -lresolv
    echo "PASS linked $target"
done <<'SLICES'
macos-arm64_x86_64 arm64 macosx arm64-apple-macos14.0
macos-arm64_x86_64 x86_64 macosx x86_64-apple-macos14.0
ios-arm64 arm64 iphoneos arm64-apple-ios16.0
ios-arm64_x86_64-simulator arm64 iphonesimulator arm64-apple-ios16.0-simulator
ios-arm64_x86_64-simulator x86_64 iphonesimulator x86_64-apple-ios16.0-simulator
tvos-arm64 arm64 appletvos arm64-apple-tvos16.0
tvos-arm64-simulator arm64 appletvsimulator arm64-apple-tvos16.0-simulator
xros-arm64 arm64 xros arm64-apple-xros1.0
xros-arm64-simulator arm64 xrsimulator arm64-apple-xros1.0-simulator
SLICES
"$output/arm64-apple-macos14.0"
