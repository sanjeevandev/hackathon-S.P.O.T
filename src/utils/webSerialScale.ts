export type SerialScaleStatus = 'disconnected' | 'connecting' | 'connected' | 'streaming' | 'error';

export interface ScaleReadout {
  weightKg: number;
  isStable: boolean;
  rawString: string;
}

/**
 * Parses raw RS-232 / USB serial ASCII output string from digital weighing indicator
 * Examples: "ST,GS,+0100.00kg", "WN: 100.5 KG", " 100.00 "
 */
export function parseScaleWeightString(rawString: string): ScaleReadout | null {
  if (!rawString || !rawString.trim()) return null;

  // Check stability flag (ST = Stable, US = Unstable)
  const isStable = !rawString.toUpperCase().includes('US');

  // Extract numerical float pattern
  const match = rawString.match(/([+-]?\d+\.?\d*)/);
  if (match) {
    const val = parseFloat(match[1]);
    if (!isNaN(val) && val >= 0) {
      return {
        weightKg: Math.round(val * 10) / 10,
        isStable,
        rawString: rawString.trim(),
      };
    }
  }
  return null;
}

/**
 * Web Serial API Manager for RS-232 / USB Weighing Scales
 */
export class WebSerialScaleManager {
  private port: any = null;
  private reader: any = null;
  private keepReading: boolean = false;

  public async connect(
    onReadout: (readout: ScaleReadout) => void,
    onStatus: (status: SerialScaleStatus, msg?: string) => void
  ): Promise<boolean> {
    onStatus('connecting', 'Requesting RS-232 / USB Serial Device...');

    if (!(navigator as any).serial) {
      onStatus('error', 'Web Serial API unavailable in current browser. Launching scale stream simulator.');
      this.startMockStream(onReadout, onStatus);
      return true;
    }

    try {
      // Request serial port from browser
      this.port = await (navigator as any).serial.requestPort();
      await this.port.open({ baudRate: 9600, dataBits: 8, stopBits: 1, parity: 'none' });

      onStatus('connected', 'RS-232 Digital Scale Connected!');

      this.keepReading = true;
      const textDecoder = new TextDecoderStream();
      this.port.readable.pipeTo(textDecoder.writable);
      this.reader = textDecoder.readable.getReader();

      onStatus('streaming', 'Live RS-232 Weight Stream Active');

      let buffer = '';
      while (this.keepReading) {
        const { value, done } = await this.reader.read();
        if (done) break;
        if (value) {
          buffer += value;
          const lines = buffer.split(/[\r\n]+/);
          buffer = lines.pop() || '';
          for (const line of lines) {
            const parsed = parseScaleWeightString(line);
            if (parsed) {
              onReadout(parsed);
            }
          }
        }
      }
      return true;
    } catch (err: any) {
      console.log('Web Serial Notice (fallback simulator active):', err);
      onStatus('error', err.message || 'Serial port connection cancelled. Launching digital scale simulator.');
      this.startMockStream(onReadout, onStatus);
      return true;
    }
  }

  public async disconnect(onStatus?: (status: SerialScaleStatus) => void) {
    this.keepReading = false;
    if (this.reader) {
      try {
        await this.reader.cancel();
      } catch (e) {}
    }
    if (this.port) {
      try {
        await this.port.close();
      } catch (e) {}
    }
    if (onStatus) onStatus('disconnected');
  }

  public startMockStream(
    onReadout: (readout: ScaleReadout) => void,
    onStatus: (status: SerialScaleStatus, msg?: string) => void
  ) {
    onStatus('streaming', 'Mock RS-232 Scale Stream Active (100.0 KG)');
    
    let baseWeight = 100.0;
    const interval = setInterval(() => {
      // Simulate minor sensor fluctuation (+/- 0.2 kg)
      const jitter = (Math.random() * 0.4 - 0.2);
      const simulatedKg = Math.round((baseWeight + jitter) * 10) / 10;
      onReadout({
        weightKg: simulatedKg,
        isStable: true,
        rawString: `ST,GS,+0${simulatedKg.toFixed(1)}kg`
      });
    }, 1200);

    return () => clearInterval(interval);
  }
}
