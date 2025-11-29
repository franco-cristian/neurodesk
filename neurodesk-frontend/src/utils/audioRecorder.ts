export class AudioRecorder {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private mediaStreamSource: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private chunks: Float32Array[] = [];
  
  // Configuración estándar para Azure Speech Services
  private readonly TARGET_SAMPLE_RATE = 16000; 

  async start(): Promise<void> {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000, // Forzamos 16kHz desde el inicio
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });
      
      const AudioContextClass = window.AudioContext || 
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.audioContext = new AudioContextClass();
      
      // Fuente de audio
      this.mediaStreamSource = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Procesador de script (Buffer Size 4096, 1 canal entrada, 1 salida)
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

      this.mediaStreamSource.connect(this.processor);
      this.processor.connect(this.audioContext.destination);

      this.chunks = [];
      
      this.processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Clonamos los datos para evitar referencias perdidas
        this.chunks.push(new Float32Array(inputData));
      };
    } catch (error) {
      console.error("Error iniciando grabadora:", error);
      throw error;
    }
  }

  async stop(): Promise<Blob> {
    if (!this.audioContext || !this.processor || !this.mediaStream) {
      throw new Error("Grabadora no inicializada");
    }

    // 1. Detener procesos
    this.processor.disconnect();
    this.mediaStreamSource?.disconnect();
    this.mediaStream.getTracks().forEach(track => track.stop());
    
    // 2. Aplanar los chunks en un solo buffer
    const totalLength = this.chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    const rawBuffer = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.chunks) {
      rawBuffer.set(chunk, offset);
      offset += chunk.length;
    }

    // 3. Downsampling a 16kHz (Crucial para Azure)
    const downsampledBuffer = this.downsampleBuffer(rawBuffer, this.audioContext.sampleRate, this.TARGET_SAMPLE_RATE);

    // 4. Codificar a WAV PCM 16-bit
    const wavBlob = this.encodeWAV(downsampledBuffer);

    await this.audioContext.close();
    this.reset();
    
    return wavBlob;
  }

  private reset() {
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.chunks = [];
  }

  // --- ALGORITMOS DE PROCESAMIENTO DE SEÑAL ---

  private downsampleBuffer(buffer: Float32Array, sampleRate: number, outSampleRate: number): Float32Array {
    if (outSampleRate === sampleRate) {
      return buffer;
    }
    
    if (outSampleRate > sampleRate) {
      console.warn("Downsampling rate mayor que sample rate original");
    }
    
    const sampleRateRatio = sampleRate / outSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    
    let offsetResult = 0;
    let offsetBuffer = 0;
    
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      
      // Promedio simple (Linear Interpolation simplificada)
      let accum = 0, count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      
      result[offsetResult] = count > 0 ? accum / count : 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    
    return result;
  }

  private encodeWAV(samples: Float32Array): Blob {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // Funciones helper para escribir strings
    const writeString = (view: DataView, offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    // 1. RIFF Header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    
    // 2. FMT Chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM Format
    view.setUint16(22, 1, true); // Mono (1 channel)
    view.setUint32(24, this.TARGET_SAMPLE_RATE, true); // Sample Rate (16000)
    view.setUint32(28, this.TARGET_SAMPLE_RATE * 2, true); // Byte Rate (SampleRate * BlockAlign)
    view.setUint16(32, 2, true); // Block Align (2 bytes per sample)
    view.setUint16(34, 16, true); // Bits Per Sample (16)

    // 3. Data Chunk
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // 4. Escribir datos PCM (Convertir Float -1.0/1.0 a Int16)
    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
      // Clamping y conversión
      let s = Math.max(-1, Math.min(1, samples[i]));
      // Escalar a rango 16-bit con signo (32767)
      s = s < 0 ? s * 0x8000 : s * 0x7FFF;
      view.setInt16(offset, s, true);
      offset += 2;
    }

    return new Blob([view], { type: 'audio/wav' });
  }
}