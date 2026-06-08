import React from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';

const MOCK_SHAP = [
  { feature: 'lactate_mean', value: 0.32 },
  { feature: 'hr_mean', value: 0.18 },
  { feature: 'temp_celsius_mean', value: 0.14 },
  { feature: 'map_mean', value: -0.11 },
  { feature: 'spo2_min', value: -0.09 },
];

export function ShapScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>SHAP Explanations</Text>
      <FlatList
        data={MOCK_SHAP}
        keyExtractor={(item) => item.feature}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text style={styles.feature}>{item.feature}</Text>
            <View style={styles.barContainer}>
              <View style={[styles.bar, {
                width: `${Math.abs(item.value) * 200}%`,
                backgroundColor: item.value > 0 ? '#ef4444' : '#22c55e',
                alignSelf: item.value > 0 ? 'flex-start' : 'flex-end',
              }]} />
            </View>
            <Text style={styles.value}>{item.value > 0 ? '+' : ''}{item.value.toFixed(2)}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 16 },
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  feature: { color: '#94a3b8', width: 140, fontSize: 12 },
  barContainer: { flex: 1, height: 16, backgroundColor: '#1e293b', borderRadius: 4 },
  bar: { height: 16, borderRadius: 4 },
  value: { color: '#f1f5f9', width: 50, textAlign: 'right', fontSize: 12 },
});
