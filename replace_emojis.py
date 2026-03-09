import os, glob

replacements = {
    '🏠': '<i class="bi bi-house-door-fill"></i>',
    '👤': '<i class="bi bi-person-fill"></i>',
    '📊': '<i class="bi bi-bar-chart-fill"></i>',
    '✏️': '<i class="bi bi-pencil-square"></i>',
    '📈': '<i class="bi bi-graph-up"></i>',
    '🏫': '<i class="bi bi-building"></i>',
    '🏆': '<i class="bi bi-trophy-fill"></i>',
    '🛡️': '<i class="bi bi-shield-lock-fill"></i>',
    '👥': '<i class="bi bi-people-fill"></i>',
    '📚': '<i class="bi bi-journal-bookmark-fill"></i>',
    '📖': '<i class="bi bi-book-half"></i>',
    '📝': '<i class="bi bi-file-earmark-text-fill"></i>',
    '🔐': '<i class="bi bi-key-fill"></i>',
    '🔌': '<i class="bi bi-plug-fill"></i>',
    '🎓': '<i class="bi bi-mortarboard-fill"></i>',
    '⚙️': '<i class="bi bi-gear-fill"></i>',
    '🗑️': '<i class="bi bi-trash-fill"></i>',
    '👀': '<i class="bi bi-eye-fill"></i>',
    '➕': '<i class="bi bi-plus-lg"></i>',
    '📥': '<i class="bi bi-box-arrow-in-down"></i>'
}

templates = glob.glob(r'c:\Users\HP\Desktop\temp\TODO\SEMESTRE_1\BDD2\projet\Projet_BDD2\templates\**\*.html', recursive=True)

for path in templates:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for emoji, icon in replacements.items():
            new_content = new_content.replace(emoji, icon)
            
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {path}")
    except Exception as e:
        print(f"Error on {path}: {e}")
