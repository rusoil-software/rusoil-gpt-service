{{- define "petra-gpt.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "petra-gpt.fullname" -}}
{{- printf "%s" (include "petra-gpt.name" .) -}}
{{- end -}}
