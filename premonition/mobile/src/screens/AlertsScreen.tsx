import React from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { getAlerts } from '../api/client';

export function AlertsScreen() {
  const { data } = useQuery({ queryKey: ['alerts'], queryFn: getAlerts, refetchInterval: 3000 });
  const alerts = (data as { alerts?: Array<{ id: string; level: string; message: string; patient_id: string }> })?.alerts ?? [];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Alert Center</Text>
      <FlatList
        data={alerts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={[styles.card, { borderLeftColor: item.level === 'RED' ? '#ef4444' : '#eab308' }]}>
            <Text style={styles.level}>{item.level}</Text>
            <Text style={styles.message}>{item.message}</Text>
            <Text style={styles.patient}>Patient: {item.patient_id}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No active alerts</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 12 },
  card: { backgroundColor: '#1e293b', padding: 14, borderRadius: 10, marginBottom: 8, borderLeftWidth: 4 },
  level: { color: '#f87171', fontWeight: 'bold' },
  message: { color: '#f1f5f9', marginTop: 4 },
  patient: { color: '#64748b', marginTop: 4, fontSize: 12 },
  empty: { color: '#64748b', textAlign: 'center', marginTop: 40 },
});
