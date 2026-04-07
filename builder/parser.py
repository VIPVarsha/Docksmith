def parse_docksmithfile(path):
    instructions = []
    with open(path) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 1:
                instructions.append((parts[0], "", line_no))
            else:
                instructions.append((parts[0], parts[1], line_no))
    return instructions