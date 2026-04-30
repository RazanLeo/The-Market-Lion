import React from 'react'
import { StatusBar } from 'expo-status-bar'
import { NavigationContainer } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Text } from 'react-native'

// Screens (stubs — will be implemented)
import DashboardScreen from './src/screens/DashboardScreen'
import SignalScreen from './src/screens/SignalScreen'
import BacktestScreen from './src/screens/BacktestScreen'
import ProfileScreen from './src/screens/ProfileScreen'
import LoginScreen from './src/screens/LoginScreen'

const Stack = createNativeStackNavigator()
const Tab = createBottomTabNavigator()
const queryClient = new QueryClient()

const GOLD = '#C9A227'
const DARK = '#0A0A0A'
const CARD = '#111111'

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: { backgroundColor: CARD, borderTopColor: '#1f1f1f' },
        tabBarActiveTintColor: GOLD,
        tabBarInactiveTintColor: '#6b7280',
        headerStyle: { backgroundColor: DARK },
        headerTintColor: GOLD,
      }}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen}
        options={{ title: 'لوحة التحكم', tabBarLabel: 'الرئيسية',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>🦁</Text> }} />
      <Tab.Screen name="Signals" component={SignalScreen}
        options={{ title: 'الإشارات', tabBarLabel: 'إشارات',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>📊</Text> }} />
      <Tab.Screen name="Backtest" component={BacktestScreen}
        options={{ title: 'الباكتستينج', tabBarLabel: 'باكتست',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>🔬</Text> }} />
      <Tab.Screen name="Profile" component={ProfileScreen}
        options={{ title: 'الحساب', tabBarLabel: 'حسابي',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>👤</Text> }} />
    </Tab.Navigator>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <NavigationContainer>
          <StatusBar style="light" />
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Main" component={MainTabs} />
          </Stack.Navigator>
        </NavigationContainer>
      </SafeAreaProvider>
    </QueryClientProvider>
  )
}
