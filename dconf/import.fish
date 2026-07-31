set -l root_dir (pwd)
find $root_dir -type f -name '*.conf' | while read f
    cat $f | dconf load (string match -rg $root_dir'(.*)'.conf $f)/
end
