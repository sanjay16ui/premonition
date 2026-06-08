import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { LoginScreen } from '../screens/LoginScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { MonitoringScreen } from '../screens/MonitoringScreen';
import { AlertsScreen } from '../screens/AlertsScreen';
import { PatientRiskScreen } from '../screens/PatientRiskScreen';
import { ShapScreen } from '../screens/ShapScreen';
import { CopilotScreen } from '../screens/CopilotScreen';
import { ExecutiveScreen } from '../screens/ExecutiveScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false, tabBarStyle: { backgroundColor: '#0f172a' }, tabBarActiveTintColor: '#38bdf8' }}>
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Monitoring" component={MonitoringScreen} />
      <Tab.Screen name="Alerts" component={AlertsScreen} />
      <Tab.Screen name="Copilot" component={CopilotScreen} />
      <Tab.Screen name="Executive" component={ExecutiveScreen} />
    </Tab.Navigator>
  );
}

export function RootNavigator({ isAuthenticated }: { isAuthenticated: boolean }) {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name="Login" component={LoginScreen} />
      ) : (
        <>
          <Stack.Screen name="Main" component={MainTabs} />
          <Stack.Screen name="PatientRisk" component={PatientRiskScreen} />
          <Stack.Screen name="Shap" component={ShapScreen} />
        </>
      )}
    </Stack.Navigator>
  );
}
