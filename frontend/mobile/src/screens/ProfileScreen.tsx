import React from 'react'
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

const GOLD = '#C9A227'; const DARK = '#0A0A0A'; const CARD = '#111111'

export default function ProfileScreen() {
  const user = { username: 'demo_trader', email: 'demo@marketlion.ai', plan: 'pro' }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: DARK }}>
      <ScrollView>
        <View style={{ padding: 16 }}>
          <Text style={{ color: GOLD, fontSize: 18, fontWeight: 'bold', marginBottom: 16 }}>👤 حسابي</Text>

          {/* Avatar & info */}
          <View style={styles.profileCard}>
            <View style={styles.avatar}>
              <Text style={{ fontSize: 28 }}>🦁</Text>
            </View>
            <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 16 }}>{user.username}</Text>
            <Text style={{ color: '#9ca3af', fontSize: 12 }}>{user.email}</Text>
            <View style={styles.planBadge}>
              <Text style={{ color: GOLD, fontWeight: 'bold', fontSize: 12 }}>
                ✦ {user.plan === 'pro' ? 'احترافي' : user.plan === 'vip' ? 'في آي بي' : 'مجاني'}
              </Text>
            </View>
          </View>

          {/* Menu items */}
          {[
            { icon: '🔔', label: 'الإشعارات', desc: 'تفعيل/إيقاف إشعارات الإشارات' },
            { icon: '🔐', label: 'الأمان', desc: 'كلمة المرور والتحقق الثنائي' },
            { icon: '💳', label: 'اشتراكي', desc: 'تجديد أو ترقية الباقة' },
            { icon: '🏦', label: 'الوسطاء', desc: 'إدارة حسابات التداول' },
            { icon: '📊', label: 'الأداء', desc: 'إحصاءات صفقاتي' },
            { icon: '🌍', label: 'اللغة', desc: 'العربية' },
            { icon: '❓', label: 'المساعدة', desc: 'الدعم الفني والتوثيق' },
          ].map(item => (
            <TouchableOpacity key={item.label} style={styles.menuItem}>
              <Text style={{ fontSize: 20, marginLeft: 12 }}>{item.icon}</Text>
              <View style={{ flex: 1 }}>
                <Text style={{ color: '#fff', fontWeight: '600' }}>{item.label}</Text>
                <Text style={{ color: '#6b7280', fontSize: 12 }}>{item.desc}</Text>
              </View>
              <Text style={{ color: '#4b5563' }}>›</Text>
            </TouchableOpacity>
          ))}

          <TouchableOpacity style={styles.logoutBtn}>
            <Text style={{ color: '#ef4444', fontWeight: 'bold' }}>تسجيل الخروج</Text>
          </TouchableOpacity>

          <Text style={{ color: '#4b5563', fontSize: 10, textAlign: 'center', marginTop: 16 }}>
            أسد السوق v2.0.0 · جميع الحقوق محفوظة 2024
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  profileCard: { backgroundColor: '#111', borderRadius: 16, padding: 20, alignItems: 'center', marginBottom: 20, borderWidth: 1, borderColor: `${GOLD}30` },
  avatar: { width: 70, height: 70, borderRadius: 35, backgroundColor: `${GOLD}20`, alignItems: 'center', justifyContent: 'center', marginBottom: 10, borderWidth: 2, borderColor: GOLD },
  planBadge: { marginTop: 8, backgroundColor: `${GOLD}15`, paddingHorizontal: 14, paddingVertical: 4, borderRadius: 20, borderWidth: 1, borderColor: `${GOLD}40` },
  menuItem: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#111', borderRadius: 12, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#1f1f1f' },
  logoutBtn: { marginTop: 12, padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#ef444440', alignItems: 'center' },
})
