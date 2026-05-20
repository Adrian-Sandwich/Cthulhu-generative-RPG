# ASCII Art Generator - Test Benchmark

## Standard Test Case

**Prompt (Medida de todas las pruebas):**
```
A dark lighthouse on a rocky coast with fog and mysterious glowing symbols carved into the stone
```

**Parameters:**
- Width: 120 characters
- Style: lovecraftian
- Model: Ollama qwen2.5:7b (or compatible)

## Expected Behavior

✅ **Success Criteria:**
1. API responds within 30-60 seconds
2. ASCII art is 80+ lines long
3. Contains recognizable lighthouse/coastal elements
4. Uses rich ASCII character palette (@%#*+=-:. )
5. Atmospheric and detailed
6. No errors or timeout

✅ **UI Behavior:**
1. Form accepts input smoothly
2. Loading spinner appears
3. Result displays in green monospace font
4. Download button works
5. Hot reload works on code changes

## Test Procedure

### Prerequisites
```bash
# Terminal 1: Check Ollama
curl http://localhost:11434/api/tags
# Should return list of available models (qwen2.5:7b minimum)

# Terminal 2: Check Flask
curl http://localhost:5001/api/health
# Should return: {"status": "ok", "service": "ascii-art-generator"}

# Terminal 3: Check React
# Navigate to http://localhost:5173
```

### Run Benchmark

1. **Open http://localhost:5173**
2. **Paste into textarea:**
   ```
   A dark lighthouse on a rocky coast with fog and mysterious glowing symbols carved into the stone
   ```
3. **Set parameters:**
   - Ancho ASCII: 120
   - Estilo: lovecraftian
4. **Click "✨ Generar ASCII Art"**
5. **Measure:**
   - Time taken (should be <60 seconds)
   - ASCII art quality (detailed? atmospheric?)
   - No errors
   - Can download result

### Success Output

Should look like:
```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~      @@@  @@@@@@@ @@@  @ @@@ @ @@@ @@@@@@
~      # %%# #      #     #     #     #
~      # #%# #      %%%%% # %%% #     %%%%%
~      # % # #      #   # #   # #     #
~      # % # #      #   # # %%# #     #
~      @@@  @@@@@@@ @@@  @ @@@  @@@@@ @@@@@
~
~  # %%%% %% % %% % %% %%%%%  # %%% %% % %%
~  #   %   %  %  %  %  %      # %   % %% % %
~  #   %   %  %  %  %  %%%%   # %%% %  %  %
~  #   %   %  %  %  %  %      # %   %     %
~  #   %   %  %  %  %  %      # %   %     %
~  #   %   %% %  %% %% %%%%%  # %%% %     %
~
~ * *% *% * *% * *% * *% * *% * *
~ # %%%% %% % % %% % %% %%%%%
~
~ %%%%%%% @@@@@ %%% %%% @@@@
~ #       %   % %  %  % %   %
~ #       %   % %  %  % %   %
~ #       @@@@ %  %  % @@@@@
~ #       %   % %  %  % %   %
~ #       %   % %  %  % %   %
~ ####### @@@@@ %%% %%% @   @
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

(Exact ASCII varies, but should be detailed and atmospheric)

## Performance Metrics

Track these metrics per test run:

| Metric | Target | Status |
|--------|--------|--------|
| Response time | <60s | ✅ |
| ASCII lines | >80 | ✅ |
| Character width | 120 | ✅ |
| Quality rating | 4/5+ | ✅ |
| No errors | 100% | ✅ |
| Download works | Yes | ✅ |
| UI responsive | Yes | ✅ |
| Hot reload | Works | ✅ |

## Regression Testing

Use this benchmark after:
- ✅ Code changes to server.py
- ✅ Prompt engineering updates
- ✅ Model switching
- ✅ Performance optimizations
- ✅ UI updates

## Notes

- Ollama model affects quality and speed
  - qwen2.5:7b: Fast, good quality (current)
  - mistral:7b: Alternative
  - neural-chat:7b: Alternative
- First run might be slower (model loading)
- Subsequent runs cached by browser (reload for fresh test)
