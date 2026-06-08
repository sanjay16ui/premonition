# PREMONITION Mobile — Build Instructions

## Prerequisites
- Node.js 20+
- Expo CLI: `npm install -g expo-cli`
- Android Studio (Android) or Xcode (iOS)

## Setup

```bash
cd mobile
npm install
```

## Development

```bash
# Start Expo dev server
npm start

# Android emulator
npm run android

# iOS simulator (macOS only)
npm run ios
```

## Environment

Create `.env`:
```
EXPO_PUBLIC_API_URL=http://YOUR_IP:8000/api/v1
```

## Tests

```bash
npm test
```

## Production Build

```bash
# Android APK
npx expo prebuild --platform android
cd android && ./gradlew assembleRelease

# iOS
npx expo prebuild --platform ios
cd ios && xcodebuild -workspace PREMONITION.xcworkspace -scheme PREMONITION -configuration Release
```

## Features
- Login with JWT
- Dashboard metrics
- Realtime ICU monitoring (5s refresh)
- Alert center
- Patient risk viewer
- SHAP feature bars
- Copilot chat
- Executive summary
- Dark mode (default)
- Offline caching via AsyncStorage
- Push notifications (expo-notifications)
