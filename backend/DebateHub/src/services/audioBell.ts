
/**
 * High-fidelity synthetic brass debate bell sound generator using Web Audio API.
 * Emulates the resonant bronze bell chime used in university debate chambers
 * (WUDC, PAUDC, KUDC).
 */

class DebateBellService {
  private ctx: AudioContext | null = null;

  private getAudioContext(): AudioContext {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return this.ctx;
  }

  // Play single brass bell strike
  playSingleBell() {
    try {
      const ctx = this.getAudioContext();
      const now = ctx.currentTime;

      // Base fundamental + rich overtone harmonics
      const frequencies = [880, 1760, 2640, 3520];
      const gains = [0.45, 0.25, 0.12, 0.05];

      frequencies.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = idx === 0 ? 'sine' : 'triangle';
        osc.frequency.setValueAtTime(freq, now);

        gain.gain.setValueAtTime(gains[idx], now);
        // Exponential decay resembling struck bell bronze
        gain.gain.exponentialRampToValueAtTime(0.0001, now + (idx === 0 ? 1.8 : 0.9));

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now);
        osc.stop(now + 2.0);
      });
    } catch (e) {
      console.warn('Audio bell error:', e);
    }
  }

  // Play double bell chime (7:00 time up)
  playDoubleBell() {
    this.playSingleBell();
    setTimeout(() => {
      this.playSingleBell();
    }, 380);
  }

  // Play continuous gavel / overtime bell (7:15 grace period exceeded)
  playOvertimeBells() {
    let count = 0;
    const interval = setInterval(() => {
      this.playSingleBell();
      count++;
      if (count >= 5) {
        clearInterval(interval);
      }
    }, 220);
  }
}

export const debateBell = new DebateBellService();


