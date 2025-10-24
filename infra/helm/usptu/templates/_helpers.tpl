{{- define "usptu.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "usptu.fullname" -}}
{{- printf "%s" (include "usptu.name" .) -}}
{{- end -}}
