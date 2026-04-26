def sincronizar_si_cambio(data_dir: str = "data"):
    """
    Comprueba si algun archivo JSON en data/ ha cambiado y sincroniza.
    Los hashes se guardan en data/.hashes_sync para persistir entre recargas.
    """
    if not st.session_state.get('github_sync'):
        return
    
    archivo_hashes = _os.path.join(data_dir, '.hashes_sync')
    
    # Cargar hashes anteriores
    hashes_anteriores = {}
    try:
        with open(archivo_hashes, 'r') as f:
            hashes_anteriores = json.load(f)
    except:
        pass
    
    archivos_json = [f for f in _os.listdir(data_dir) if f.endswith('.json')]
    hashes_actuales = {}
    algo_cambio = False
    
    for archivo in archivos_json:
        ruta = _os.path.join(data_dir, archivo)
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            hash_actual = _hashlib.md5(contenido.encode()).hexdigest()
            hashes_actuales[archivo] = hash_actual
            
            if archivo not in hashes_anteriores:
                algo_cambio = True
            elif hashes_anteriores[archivo] != hash_actual:
                algo_cambio = True
        except:
            pass
    
    # Guardar hashes actuales
    try:
        with open(archivo_hashes, 'w') as f:
            json.dump(hashes_actuales, f)
    except:
        pass
    
    if algo_cambio:
        try:
            st.session_state.github_sync.sync_all_data_files(data_dir)
        except Exception as e:
            print(f"Error en auto-sync: {e}")
