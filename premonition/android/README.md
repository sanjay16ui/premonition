# PREMONITION Android

Native Android project is generated via Expo prebuild from `mobile/`.

## Generate

```bash
cd mobile
npm install
npx expo prebuild --platform android
```

This creates `mobile/android/` with Gradle project. Symlink or copy to this directory for CI.

## Build Release APK

```bash
cd mobile/android
./gradlew assembleRelease
```

## Package

`health.premonition.mobile` (configured in `mobile/app.json`)
