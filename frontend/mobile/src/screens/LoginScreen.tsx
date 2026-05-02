import React, { useState } from 'react'
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { useNavigation } from '@react-navigation/native'

const GOLD = '#C9A227'; const DARK = '#0A0A0A'; const CARD = '#111111'; const BORDER = '#1f1f1f'

export default function LoginScreen() {
  const navigation = useNavigation<any>()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    if (!email || !password) {
      setError('الرجاء إدخال البريد وكلمة المرور')
      return
    }
    setLoading(true)
    setError('')
    try {
      // For demo: any credentials work
      await new Promise(res => setTimeout(res, 800))
      navigation.replace('Main')
    } catch {
      setError('خطأ في تسجيل الدخول')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: DARK }}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <View style={styles.container}>
          {/* Logo */}
          <Text style={styles.lion}>🦁</Text>
          <Text style={styles.appName}>أسد السوق</Text>
          <Text style={styles.tagline}>نظام التداول بالذكاء الاصطناعي</Text>

          {error ? (
            <View style={styles.errorBox}>
              <Text style={{ color: '#ef4444', fontSize: 13 }}>{error}</Text>
            </View>
          ) : null}

          <View style={styles.form}>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="البريد الإلكتروني"
              placeholderTextColor="#4b5563"
              style={styles.input}
              keyboardType="email-address"
              autoCapitalize="none"
              textDirection="ltr"
            />
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="كلمة المرور"
              placeholderTextColor="#4b5563"
              style={styles.input}
              secureTextEntry
            />
            <TouchableOpacity style={styles.loginBtn} onPress={handleLogin} disabled={loading}>
              <Text style={styles.loginBtnText}>
                {loading ? 'جاري الدخول...' : 'دخول 🦁'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => navigation.replace('Main')}>
              <Text style={styles.demoLink}>تجربة بدون تسجيل (وضع تجريبي)</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.footer}>
            للتجربة: أي بريد إلكتروني وكلمة مرور
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  lion: { fontSize: 64, marginBottom: 8 },
  appName: { color: GOLD, fontSize: 28, fontWeight: 'bold', marginBottom: 4 },
  tagline: { color: '#6b7280', fontSize: 14, marginBottom: 32 },
  errorBox: { backgroundColor: '#ef444420', borderRadius: 8, padding: 12, marginBottom: 16, width: '100%', borderWidth: 1, borderColor: '#ef444440' },
  form: { width: '100%' },
  input: { backgroundColor: CARD, borderWidth: 1, borderColor: BORDER, borderRadius: 12, padding: 14, color: '#fff', fontSize: 14, marginBottom: 12, textAlign: 'right' },
  loginBtn: { backgroundColor: GOLD, borderRadius: 12, padding: 16, alignItems: 'center', marginBottom: 12 },
  loginBtnText: { color: '#0A0A0A', fontWeight: 'bold', fontSize: 16 },
  demoLink: { color: '#6b7280', textAlign: 'center', fontSize: 13, textDecorationLine: 'underline' },
  footer: { position: 'absolute', bottom: 20, color: '#374151', fontSize: 11 },
})
