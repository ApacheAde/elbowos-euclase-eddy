# Euclase Eddy

Full-colour Python 3 neon tide-hopper for [ElbowOS](https://x.com/ElbowOS).

A pale-blue crystal newt hops seven eddy lanes. Amber kelp rafts drift both ways. Coral eels sting. Gold coins sit on some rafts. Reach the crystal shelf for a bank bonus, then the current speeds up.

Not a ROM, not an emulator, original rules and art.

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 euclase_eddy.py --play
```

Controls: A / D or arrows sidestep, W / Up / Space hop up, S / Down hop back, R restart.

## Record a 9:16 reel

```bash
python3 euclase_eddy.py --record
```

Writes a 1080x1920, 15s, 30fps H.264 MP4 (dummy SDL video driver). Override the path with `ELBOWOS_MP4`.

## Links

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/1o_oNMRod3ccMp10_eVpaU1as1b8BeKZp/view
- Repo: https://github.com/ApacheAde/elbowos-euclase-eddy
