import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { getExecutiveSummary } from '../api/client';

export function ExecutiveScreen() {
  const { data, isLoading } = useQuery({ queryKey: ['executive'], queryFn: getExecutiveSummary });
  const summary = (data as { message?: string })?.message ?? '';

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Executive Dashboard</Text>
      {isLoading ? (
        <Text style={styles.muted}>Generating executive summary...</Text>
      ) : (
        <Text style={styles.summary}>{summary || 'Hospital operations within normal parameters.'}</Text>
      )}
      <View style={styles.kpiRow}>
        {['Occupancy', 'Sepsis Rate', 'Alert Response', 'Model Uptime'].map((kpi) => (
          <View key={kpi} style={styles.kpiCard}>
            <Text style={styles.kpiLabel}>{kpi}</Text>
            <Text style={styles.kpiValue}>—</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#f1f5f9' },
  summary: { color: '#cbd5e1', marginTop: 16, lineHeight: 22 },
  muted: { color: '#64748b', marginTop: 16 },
  kpiRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 24 },
  kpiCard: { backgroundColor: '#1e293b', padding: 16, borderRadius: 12, width: '47%' },
  kpiLabel: { color: '#94a3b8', fontSize: 12 },
  kpiValue: { color: '#38bdf8', fontSize: 24, fontWeight: 'bold', marginTop: 4 },
});
