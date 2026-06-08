import React, { useEffect } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useCacheStore } from '../store/cacheStore';

export function MonitoringScreen() {
  const { data } = useQuery({
    queryKey: ['monitoring'],
    queryFn: async () => {
      const { data: d } = await apiClient.get('/realtime/patients');
      return d;
    },
    refetchInterval: 5000,
  });
  const setPatients = useCacheStore((s) => s.setPatients);

  useEffect(() => {
    if (data) setPatients(data as Record<string, unknown>);
  }, [data, setPatients]);

  const patients = (data as { patients?: Array<{ id: string; risk_score: number; alert_level: string }> })?.patients ?? [];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Live ICU Monitoring</Text>
      <FlatList
        data={patients}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.patientId}>{item.id}</Text>
            <Text style={styles.risk}>Risk: {(item.risk_score * 100).toFixed(1)}%</Text>
            <Text style={[styles.level, { color: levelColor(item.alert_level) }]}>{item.alert_level}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No active patients</Text>}
      />
    </View>
  );
}

function levelColor(level: string) {
  const map: Record<string, string> = { GREEN: '#22c55e', YELLOW: '#eab308', ORANGE: '#f97316', RED: '#ef4444', BLACK: '#1e1e1e' };
  return map[level] ?? '#94a3b8';
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 12 },
  card: { backgroundColor: '#1e293b', padding: 14, borderRadius: 10, marginBottom: 8 },
  patientId: { color: '#f1f5f9', fontWeight: '600' },
  risk: { color: '#94a3b8', marginTop: 4 },
  level: { fontWeight: 'bold', marginTop: 4 },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 40 },
});
