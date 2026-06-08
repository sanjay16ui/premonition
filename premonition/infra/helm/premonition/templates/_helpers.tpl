{{- define "premonition.name" -}}
premonition
{{- end }}

{{- define "premonition.fullname" -}}
{{ include "premonition.name" . }}-api
{{- end }}

{{- define "premonition.labels" -}}
app.kubernetes.io/name: {{ include "premonition.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
{{- end }}

{{- define "premonition.selectorLabels" -}}
app.kubernetes.io/name: {{ include "premonition.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
