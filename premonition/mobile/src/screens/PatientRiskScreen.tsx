import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { getPatientRisk } from '../api/client';

export function PatientRiskScreen({ route }: { route: { params: { patientId: string } } }) {
  const patientId = route?.params?.patientId ?? 'patient-001';
  const { data, isLoading } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => getPatientRisk(patientId),
  });

  const patient = data as { id?: string; risk_score?: number; alert_level?: string; vitals?: Record<string, number> } | undefined;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Patient Risk Viewer</Text>
      {isLoading ? (
        <Text style={styles.muted}>Loading...</Text>
      ) : (
        <>
          <Text style={styles.id}>{patient?.id ?? patientId}</Text>
          <Text style={styles.risk}>Risk Score: {((patient?.risk_score ?? 0) * 100).toFixed(1)}%</Text>
          <Text style={styles.level}>Alert Level: {patient?.alert_level ?? 'GREEN'}</Text>
          {patient?.vitals && Object.entries(patient.vitals).map(([k, v]) => (
            <Text key={k} style={styles.vital}>{k}: {v}</Text>
          ))}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#f1f5f9' },
  id: { color: '#38bdf8', fontSize: 18, marginTop: 16 },
  risk: { color: '#f1f5f9', fontSize: 28, fontWeight: 'bold', marginTop: 12 },
  level: { color: '#eab308', marginTop: 8 },
  vital: { color: '#94a3b8', marginTop: 4 },
  muted: { color: '#64748b', marginTop: 20 },
});
