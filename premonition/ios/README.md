# PREMONITION iOS

Native iOS project is generated via Expo prebuild from `mobile/`.

## Generate

```bash
cd mobile
npm install
npx expo prebuild --platform ios
```

This creates `mobile/ios/` with Xcode workspace.

## Build (macOS + Xcode required)

```bash
cd mobile/ios
xcodebuild -workspace PREMONITION.xcworkspace -scheme PREMONITION -configuration Release
```

## Bundle ID

`health.premonition.mobile` (configured in `mobile/app.json`)
