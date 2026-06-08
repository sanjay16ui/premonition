import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { getDashboardMetrics } from '../api/client';
import { useThemeStore } from '../store/themeStore';

export function DashboardScreen() {
  const isDark = useThemeStore((s) => s.isDark);
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardMetrics });

  const bg = isDark ? '#0f172a' : '#f8fafc';
  const card = isDark ? '#1e293b' : '#fff';
  const text = isDark ? '#f1f5f9' : '#0f172a';

  return (
    <ScrollView style={[styles.container, { backgroundColor: bg }]}>
      <Text style={[styles.title, { color: text }]}>Command Dashboard</Text>
      {isLoading ? (
        <Text style={{ color: '#94a3b8' }}>Loading metrics...</Text>
      ) : (
        <View style={styles.grid}>
          {['total_predictions', 'high_risk_count', 'model_accuracy', 'active_patients'].map((key) => (
            <View key={key} style={[styles.card, { backgroundColor: card }]}>
              <Text style={[styles.cardLabel, { color: '#94a3b8' }]}>{key.replace(/_/g, ' ')}</Text>
              <Text style={[styles.cardValue, { color: '#38bdf8' }]}>
                {String((data as Record<string, unknown>)?.[key] ?? '—')}
              </Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 16 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  card: { width: '47%', padding: 16, borderRadius: 12 },
  cardLabel: { fontSize: 12, textTransform: 'capitalize' },
  cardValue: { fontSize: 24, fontWeight: 'bold', marginTop: 4 },
});
