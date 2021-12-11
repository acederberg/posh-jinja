
rm -r build 
mkdir build
python3 render.py my_theme.omp.yaml.j2 my_palette.yaml
python3 tools.py ./build/my_theme.omp.yaml
