#!/usr/bin/env bash
# Note: requires jq, fuzzel, wpctl (wireplumber)

pw-dump | \
jq -r '
  .[] 
  | select(.info.props["media.class"] == "Audio/Sink" and .info.props["node.virtual"] != true)
  | .id as $id 
  | .info.props["node.description"] as $name 
  | .info.props["device.icon-name"] as $icon 
  | "\($id)::\($name)::\($icon)"
' | \
sed 's/audio-card-analog/audio-card/g' | \
while IFS= read -r line; do
    if [[ $line =~ ^([0-9]+)::(.+)::(.+)$ ]]; then
        id="${BASH_REMATCH[1]}"
        name="${BASH_REMATCH[2]}"
        icon="${BASH_REMATCH[3]}"
        printf '%s\t%s\0icon\x1f%s\n' "$id" "$name" "$icon"
    fi
done | \
fuzzel --dmenu \
       --with-nth=2 \
       --prompt="Audio output: " | \
awk '{print $1}' | \
xargs -r wpctl set-default
