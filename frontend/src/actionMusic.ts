
export class ActionMusic {
  private ctx: AudioContext | null = null;
  private timer: number | null = null;
  private step = 0;
  private enabled = false;

  private tone(
    frequency: number,
    duration: number,
    volume: number,
    type: OscillatorType = "sine"
  ) {
    if (!this.ctx) return;

    const ctx = this.ctx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = type;
    osc.frequency.value = frequency;

    const now = ctx.currentTime;

    gain.gain.setValueAtTime(volume, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + duration);
  }

  start() {
    if (this.enabled) return;

    this.ctx ??= new AudioContext();
    void this.ctx.resume();
    this.enabled = true;

    const bass = [55, 55, 65.41, 55, 73.42, 65.41, 49, 55];
    const melody = [220, 0, 261.63, 0, 293.66, 261.63, 196, 0];

    this.timer = window.setInterval(() => {
      if (!this.enabled) return;

      const index = this.step % bass.length;

      this.tone(bass[index], 0.22, 0.045, "sawtooth");

      if (this.step % 2 === 0) {
        this.tone(110, 0.09, 0.025, "triangle");
      }

      if (melody[index]) {
        this.tone(melody[index], 0.16, 0.014, "square");
      }

      this.step++;
    }, 240);
  }

  stop() {
    this.enabled = false;

    if (this.timer !== null) {
      window.clearInterval(this.timer);
      this.timer = null;
    }
  }

  dispose() {
    this.stop();
    if (this.ctx) {
      void this.ctx.close();
      this.ctx = null;
    }
  }
}
