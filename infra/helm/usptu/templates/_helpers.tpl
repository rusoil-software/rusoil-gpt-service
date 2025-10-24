{{- define "rusoilgpt.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "rusoilgpt.fullname" -}}
{{- printf "%s" (include "rusoilgpt.name" .) -}}
{{- end -}}
