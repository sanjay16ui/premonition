import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { copilotChat } from '../api/client';

interface Message { role: string; content: string }

export function CopilotScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const res = await copilotChat(userMsg);
      setMessages((m) => [...m, { role: 'assistant', content: res.message }]);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'Unable to reach copilot.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Text style={styles.title}>Clinical AI Copilot</Text>
      <FlatList
        data={messages}
        keyExtractor={(_, i) => String(i)}
        style={styles.list}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.aiBubble]}>
            <Text style={styles.bubbleText}>{item.content}</Text>
          </View>
        )}
      />
      <View style={styles.inputRow}>
        <TextInput style={styles.input} value={input} onChangeText={setInput} placeholder="Ask the copilot..." placeholderTextColor="#64748b" />
        <TouchableOpacity style={styles.sendBtn} onPress={send} disabled={loading}>
          <Text style={styles.sendText}>{loading ? '...' : 'Send'}</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#f1f5f9', marginBottom: 8 },
  list: { flex: 1 },
  bubble: { padding: 12, borderRadius: 12, marginBottom: 8, maxWidth: '85%' },
  userBubble: { backgroundColor: '#0284c7', alignSelf: 'flex-end' },
  aiBubble: { backgroundColor: '#1e293b', alignSelf: 'flex-start' },
  bubbleText: { color: '#f1f5f9' },
  inputRow: { flexDirection: 'row', gap: 8, marginTop: 8 },
  input: { flex: 1, backgroundColor: '#1e293b', color: '#f1f5f9', padding: 12, borderRadius: 8 },
  sendBtn: { backgroundColor: '#0284c7', padding: 12, borderRadius: 8, justifyContent: 'center' },
  sendText: { color: '#fff', fontWeight: '600' },
});
