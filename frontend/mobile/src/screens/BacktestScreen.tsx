import React from 'react'
import { View, Text, StyleSheet, ScrollView } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

const GOLD = '#C9A227'; const DARK = '#0A0A0A'; const CARD = '#111111'; const BULL = '#10a33a'; const BEAR = '#ef4444'

const DEMO_STATS = [
  { label: 'عدد الصفقات', value: '142', color: '#fff' },
  { label: 'Win Rate', value: '67.6%', color: BULL },
  { label: 'Profit Factor', value: '2.8', color: GOLD },
  { label: 'Sharpe', value: '1.9', color: GOLD },
  { label: 'Max DD', value: '8.4%', color: BEAR },
  { label: 'صافي الربح', value: '$5,840', color: BULL },
  { label: 'العائد', value: '58.4%', color: BULL },
  { label: 'Calmar', value: '6.9', color: GOLD },
]

export default function BacktestScreen() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: DARK }}>
      <ScrollView>
        <View style={{ padding: 16 }}>
          <Text style={{ color: GOLD, fontSize: 18, fontWeight: 'bold', marginBottom: 4 }}>🔬 الباكتستينج</Text>
          <Text style={{ color: '#6b7280', fontSize: 12, marginBottom: 16 }}>نتائج اختبار XAUUSD H1 · 2023</Text>

          {/* Stats grid */}
          <View style={styles.grid}>
            {DEMO_STATS.map(s => (
              <View key={s.label} style={styles.statCard}>
                <Text style={[styles.statValue, { color: s.color }]}>{s.value}</Text>
                <Text style={styles.statLabel}>{s.label}</Text>
              </View>
            ))}
          </View>

          <View style={styles.notice}>
            <Text style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center' }}>
              للوصول الكامل للباكتستينج مع الباقة الاحترافية أو فأعلى
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  statCard: { width: '47%', backgroundColor: CARD, borderRadius: 10, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: '#1f1f1f' },
  statValue: { fontSize: 20, fontWeight: 'bold' },
  statLabel: { color: '#6b7280', fontSize: 12, marginTop: 4 },
  notice: { marginTop: 20, padding: 16, backgroundColor: CARD, borderRadius: 12, borderWidth: 1, borderColor: `${GOLD}30` },
})
