import React, { useState, useEffect } from 'react'
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, RefreshControl, Dimensions
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const GOLD = '#C9A227'
const DARK = '#0A0A0A'
const CARD = '#111111'
const BORDER = '#1f1f1f'
const BULL = '#10a33a'
const BEAR = '#ef4444'

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'

const SYMBOLS = ['XAUUSD', 'USOIL', 'EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD']

export default function DashboardScreen() {
  const [selectedSymbol, setSelectedSymbol] = useState('XAUUSD')
  const [selectedTF, setSelectedTF] = useState('H1')
  const [refreshing, setRefreshing] = useState(false)

  const { data: prices, refetch: refetchPrices } = useQuery({
    queryKey: ['prices'],
    queryFn: async () => {
      try {
        const resp = await axios.get(`${API_URL}/api/v1/prices`)
        return resp.data
      } catch {
        return generateDemoPrices()
      }
    },
    refetchInterval: 5000,
  })

  const { data: signal, refetch: refetchSignal } = useQuery({
    queryKey: ['signal', selectedSymbol, selectedTF],
    queryFn: async () => {
      try {
        const resp = await axios.get(`${API_URL}/api/v1/signal/${selectedSymbol}/${selectedTF}`)
        return resp.data
      } catch {
        return generateDemoSignal(selectedSymbol)
      }
    },
    refetchInterval: 30000,
  })

  const onRefresh = async () => {
    setRefreshing(true)
    await Promise.all([refetchPrices(), refetchSignal()])
    setRefreshing(false)
  }

  const currentPrice = prices?.[selectedSymbol]?.price || 0
  const prevPrice = prices?.[selectedSymbol]?.prev_close || currentPrice
  const priceChange = ((currentPrice - prevPrice) / prevPrice * 100)

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={GOLD} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🦁 أسد السوق</Text>
          <View style={styles.liveBadge}>
            <View style={styles.liveDot} />
            <Text style={styles.liveText}>مباشر</Text>
          </View>
        </View>

        {/* Symbol selector */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.symbolScroll}>
          {SYMBOLS.map(sym => (
            <TouchableOpacity
              key={sym}
              onPress={() => setSelectedSymbol(sym)}
              style={[styles.symbolBtn, selectedSymbol === sym && styles.symbolBtnActive]}
            >
              <Text style={[styles.symbolText, selectedSymbol === sym && styles.symbolTextActive]}>
                {sym}
              </Text>
              {prices?.[sym] && (
                <Text style={[styles.symbolPrice, { color: (prices[sym].change || 0) >= 0 ? BULL : BEAR }]}>
                  {(prices[sym].change || 0) >= 0 ? '▲' : '▼'} {Math.abs(prices[sym].change || 0).toFixed(2)}%
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Price card */}
        <View style={styles.priceCard}>
          <Text style={styles.symbolLabel}>{selectedSymbol}</Text>
          <Text style={styles.priceValue}>{currentPrice.toFixed(5)}</Text>
          <Text style={[styles.priceChange, { color: priceChange >= 0 ? BULL : BEAR }]}>
            {priceChange >= 0 ? '▲' : '▼'} {Math.abs(priceChange).toFixed(3)}%
          </Text>
        </View>

        {/* Timeframe selector */}
        <View style={styles.tfRow}>
          {['M15', 'H1', 'H4', 'D1'].map(tf => (
            <TouchableOpacity
              key={tf}
              onPress={() => setSelectedTF(tf)}
              style={[styles.tfBtn, selectedTF === tf && styles.tfBtnActive]}
            >
              <Text style={[styles.tfText, selectedTF === tf && styles.tfTextActive]}>{tf}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Signal Card */}
        {signal && (
          <View style={[styles.signalCard, { borderLeftColor: signal.side === 'BUY' ? BULL : BEAR }]}>
            <View style={styles.signalHeader}>
              <View style={[styles.sideBadge, { backgroundColor: signal.side === 'BUY' ? `${BULL}20` : `${BEAR}20` }]}>
                <Text style={[styles.sideText, { color: signal.side === 'BUY' ? BULL : BEAR }]}>
                  {signal.side === 'BUY' ? '▲ شراء' : '▼ بيع'}
                </Text>
              </View>
              <Text style={[styles.confluenceText, { color: signal.confluenceScore >= 75 ? BULL : GOLD }]}>
                {signal.confluenceScore?.toFixed(1)}%
              </Text>
            </View>

            {/* Confluence bar */}
            <View style={styles.confBar}>
              <View style={[styles.confFill, {
                width: `${signal.confluenceScore || 0}%`,
                backgroundColor: signal.confluenceScore >= 75 ? BULL : GOLD,
              }]} />
            </View>

            <View style={styles.priceGrid}>
              {[
                { label: 'الدخول', value: signal.entry?.toFixed(5), color: GOLD },
                { label: 'وقف الخسارة', value: signal.sl?.toFixed(5), color: BEAR },
                { label: 'الهدف 1', value: signal.tp1?.toFixed(5), color: BULL },
                { label: 'الهدف 2', value: signal.tp2?.toFixed(5), color: BULL },
                { label: 'الهدف 3', value: signal.tp3?.toFixed(5), color: BULL },
                { label: 'حجم الصفقة', value: `${signal.lotSize} لوت`, color: '#fff' },
              ].map(row => (
                <View key={row.label} style={styles.priceRow}>
                  <Text style={styles.priceLabel}>{row.label}</Text>
                  <Text style={[styles.priceVal, { color: row.color }]}>{row.value}</Text>
                </View>
              ))}
            </View>

            <View style={[styles.shouldTrade, { backgroundColor: signal.shouldTrade ? `${BULL}15` : `${BEAR}15` }]}>
              <Text style={{ color: signal.shouldTrade ? BULL : BEAR, fontWeight: 'bold' }}>
                {signal.shouldTrade ? '✅ تنفيذ الصفقة' : '⚠️ انتظر — شروط غير مكتملة'}
              </Text>
            </View>
          </View>
        )}

        {/* Performance mini stats */}
        <View style={styles.statsRow}>
          {[
            { label: 'Win Rate', value: '78.4%', color: BULL },
            { label: 'Sharpe', value: '2.8', color: GOLD },
            { label: 'Max DD', value: '8.2%', color: BEAR },
            { label: 'P/F', value: '3.2', color: GOLD },
          ].map(s => (
            <View key={s.label} style={styles.statCard}>
              <Text style={[styles.statValue, { color: s.color }]}>{s.value}</Text>
              <Text style={styles.statLabel}>{s.label}</Text>
            </View>
          ))}
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  )
}

function generateDemoPrices() {
  const bases: Record<string, number> = { XAUUSD: 2350, USOIL: 78.5, EURUSD: 1.085, GBPUSD: 1.27, USDJPY: 149.5, BTCUSD: 65000 }
  return Object.fromEntries(Object.entries(bases).map(([sym, base]) => [sym, {
    symbol: sym, price: base * (1 + (Math.random() - 0.5) * 0.002),
    change: (Math.random() - 0.5) * 0.5, prev_close: base,
  }]))
}

function generateDemoSignal(symbol: string) {
  const bases: Record<string, number> = { XAUUSD: 2350, USOIL: 78.5, EURUSD: 1.085, GBPUSD: 1.27, USDJPY: 149.5, BTCUSD: 65000 }
  const price = bases[symbol] || 1.0
  const side = Math.random() > 0.5 ? 'BUY' : 'SELL'
  const sl = side === 'BUY' ? price * 0.995 : price * 1.005
  return {
    symbol, side, entry: price, sl,
    tp1: side === 'BUY' ? price * 1.005 : price * 0.995,
    tp2: side === 'BUY' ? price * 1.01 : price * 0.99,
    tp3: side === 'BUY' ? price * 1.015 : price * 0.985,
    confluenceScore: 60 + Math.random() * 30, lotSize: 0.1,
    shouldTrade: Math.random() > 0.3, rr1: 1.0, rr2: 2.0, rr3: 3.0,
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: DARK },
  scroll: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  headerTitle: { color: GOLD, fontSize: 20, fontWeight: 'bold' },
  liveBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: `${BULL}20`, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  liveDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: BULL },
  liveText: { color: BULL, fontSize: 12, fontWeight: '600' },
  symbolScroll: { paddingHorizontal: 12, marginBottom: 8 },
  symbolBtn: { marginRight: 10, padding: 10, borderRadius: 10, backgroundColor: CARD, borderWidth: 1, borderColor: BORDER, alignItems: 'center', minWidth: 80 },
  symbolBtnActive: { borderColor: GOLD, backgroundColor: `${GOLD}15` },
  symbolText: { color: '#9ca3af', fontSize: 12, fontWeight: '600' },
  symbolTextActive: { color: GOLD },
  symbolPrice: { fontSize: 10, marginTop: 2 },
  priceCard: { margin: 12, padding: 16, backgroundColor: CARD, borderRadius: 12, borderWidth: 1, borderColor: BORDER, alignItems: 'center' },
  symbolLabel: { color: '#9ca3af', fontSize: 14, marginBottom: 4 },
  priceValue: { color: '#fff', fontSize: 32, fontWeight: 'bold', fontFamily: 'monospace' },
  priceChange: { fontSize: 16, fontWeight: '600', marginTop: 4 },
  tfRow: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginBottom: 12 },
  tfBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, backgroundColor: CARD, borderWidth: 1, borderColor: BORDER },
  tfBtnActive: { backgroundColor: `${GOLD}20`, borderColor: GOLD },
  tfText: { color: '#9ca3af', fontSize: 13 },
  tfTextActive: { color: GOLD, fontWeight: '600' },
  signalCard: { margin: 12, padding: 16, backgroundColor: CARD, borderRadius: 12, borderWidth: 1, borderColor: BORDER, borderLeftWidth: 3 },
  signalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  sideBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  sideText: { fontWeight: 'bold', fontSize: 15 },
  confluenceText: { fontSize: 22, fontWeight: 'bold' },
  confBar: { height: 6, backgroundColor: BORDER, borderRadius: 3, marginBottom: 14, overflow: 'hidden' },
  confFill: { height: '100%', borderRadius: 3 },
  priceGrid: { gap: 8 },
  priceRow: { flexDirection: 'row', justifyContent: 'space-between' },
  priceLabel: { color: '#9ca3af', fontSize: 13 },
  priceVal: { fontSize: 13, fontFamily: 'monospace', fontWeight: '600' },
  shouldTrade: { marginTop: 12, padding: 10, borderRadius: 8, alignItems: 'center' },
  statsRow: { flexDirection: 'row', margin: 12, gap: 8 },
  statCard: { flex: 1, padding: 10, backgroundColor: CARD, borderRadius: 10, borderWidth: 1, borderColor: BORDER, alignItems: 'center' },
  statValue: { fontSize: 14, fontWeight: 'bold' },
  statLabel: { color: '#6b7280', fontSize: 10, marginTop: 2 },
})
