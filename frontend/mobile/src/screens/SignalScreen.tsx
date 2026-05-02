import React, { useState } from 'react'
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

const GOLD = '#C9A227'; const DARK = '#0A0A0A'; const CARD = '#111111'
const BORDER = '#1f1f1f'; const BULL = '#10a33a'; const BEAR = '#ef4444'

const DEMO_SIGNALS = [
  { id: 1, symbol: 'XAUUSD', tf: 'H1', side: 'BUY', score: 84.2, entry: 2351.50, sl: 2340.00, tp3: 2385.00, time: '14:32', shouldTrade: true },
  { id: 2, symbol: 'EURUSD', tf: 'H4', side: 'SELL', score: 76.8, entry: 1.0845, sl: 1.0890, tp3: 1.0750, time: '13:15', shouldTrade: true },
  { id: 3, symbol: 'GBPUSD', tf: 'H1', side: 'BUY', score: 71.4, entry: 1.2720, sl: 1.2680, tp3: 1.2840, time: '12:00', shouldTrade: false },
  { id: 4, symbol: 'USOIL', tf: 'D1', side: 'SELL', score: 65.5, entry: 78.45, sl: 80.20, tp3: 74.00, time: '09:00', shouldTrade: false },
]

export default function SignalScreen() {
  const [filter, setFilter] = useState('all')
  const filtered = filter === 'all' ? DEMO_SIGNALS
    : filter === 'buy' ? DEMO_SIGNALS.filter(s => s.side === 'BUY')
    : DEMO_SIGNALS.filter(s => s.side === 'SELL')

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: DARK }}>
      <View style={styles.header}>
        <Text style={styles.title}>📊 الإشارات</Text>
      </View>
      <View style={styles.filterRow}>
        {['all', 'buy', 'sell'].map(f => (
          <TouchableOpacity key={f} onPress={() => setFilter(f)} style={[styles.filterBtn, filter === f && styles.filterActive]}>
            <Text style={[styles.filterText, filter === f && { color: GOLD }]}>
              {f === 'all' ? 'الكل' : f === 'buy' ? '▲ شراء' : '▼ بيع'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <ScrollView style={{ padding: 12 }}>
        {filtered.map(s => (
          <View key={s.id} style={[styles.card, { borderLeftColor: s.side === 'BUY' ? BULL : BEAR }]}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardSymbol}>{s.symbol} · {s.tf}</Text>
              <Text style={[styles.cardSide, { color: s.side === 'BUY' ? BULL : BEAR }]}>
                {s.side === 'BUY' ? '▲ شراء' : '▼ بيع'}
              </Text>
            </View>
            <View style={styles.cardBody}>
              <View>
                <Text style={styles.cardLabel}>الدخول</Text>
                <Text style={[styles.cardValue, { color: GOLD }]}>{s.entry.toFixed(s.entry > 100 ? 2 : 4)}</Text>
              </View>
              <View>
                <Text style={styles.cardLabel}>SL</Text>
                <Text style={[styles.cardValue, { color: BEAR }]}>{s.sl.toFixed(s.sl > 100 ? 2 : 4)}</Text>
              </View>
              <View>
                <Text style={styles.cardLabel}>TP3</Text>
                <Text style={[styles.cardValue, { color: BULL }]}>{s.tp3.toFixed(s.tp3 > 100 ? 2 : 4)}</Text>
              </View>
              <View style={{ alignItems: 'center' }}>
                <Text style={styles.cardLabel}>توافق</Text>
                <Text style={[styles.cardValue, { color: s.score >= 75 ? BULL : GOLD }]}>{s.score}%</Text>
              </View>
            </View>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
              <Text style={{ color: s.shouldTrade ? BULL : '#6b7280', fontSize: 12 }}>
                {s.shouldTrade ? '✅ تنفيذ' : '⚠️ انتظر'}
              </Text>
              <Text style={{ color: '#4b5563', fontSize: 12 }}>{s.time}</Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  header: { padding: 16, borderBottomWidth: 1, borderBottomColor: BORDER },
  title: { color: GOLD, fontSize: 18, fontWeight: 'bold' },
  filterRow: { flexDirection: 'row', padding: 12, gap: 8 },
  filterBtn: { flex: 1, padding: 8, borderRadius: 8, backgroundColor: CARD, borderWidth: 1, borderColor: BORDER, alignItems: 'center' },
  filterActive: { borderColor: GOLD, backgroundColor: `${GOLD}15` },
  filterText: { color: '#9ca3af', fontWeight: '600' },
  card: { backgroundColor: CARD, borderRadius: 12, padding: 14, marginBottom: 10, borderLeftWidth: 3, borderWidth: 1, borderColor: BORDER },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  cardSymbol: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  cardSide: { fontWeight: 'bold', fontSize: 14 },
  cardBody: { flexDirection: 'row', justifyContent: 'space-between' },
  cardLabel: { color: '#6b7280', fontSize: 11, marginBottom: 2 },
  cardValue: { fontFamily: 'monospace', fontWeight: 'bold', fontSize: 13 },
})
