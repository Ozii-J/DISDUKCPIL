dependencies = [
    "streamlit",
    "pandas",
    "plotly",
    "numpy",
    "os"  # Tidak perlu ditambahkan karena sudah built-in di Python
]

with open("requirements.txt", "w") as f:
    f.write("\n".join(dependencies))

print("File requirements.txt telah dibuat.")
