# Groundstation

    pip install -e .

## Writing/Uploading Scripts


``` python
from rosen.axe import AXEScript
from rosen.gcomm import GCOMMScript

a = AXEScript()
a.execute('eduplsb', 'foo_command')
a.statement('eduplsb', foo=[1, 2, 3])
a.query('dcm', ['thermistor1', 'thermistor2'])
a.set('qcb', bar=123)

g = GCOMMScript()
g.schedule_script(a)
g.save('myscript.pkl')
```

## Executing GCOMM Scripts

    $ rosen run myscript.pkl
