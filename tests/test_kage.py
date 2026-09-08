from tekken_assistant.data.kage import parse_combos

FIXTURE = """
<ul class="collection">
<li class="combo-item jin-combo v3.02" id="combo-2489">
  <div class="combo">
    <div class="powered">
      <div><img alt="x"><strong>7 hits</strong> | <strong>73 damages</strong></div>
    </div>
    <div class="title-combo"><span class="title">Jin</span></div>
    <p class="comboImg">
      <span dataname='d/f' key='1'>d/f</span><span dataname='2' key='2'>2</span>
      <span dataname=' ' key='4'>break</span><span dataname='W!' key='5'>W!</span>
      <span dataname=' ' key='6'>break</span><span dataname='f' key='7'>f</span>
      <span dataname='N' key='8'>N</span><span dataname='d' key='9'>d</span>
      <span dataname='d/f' key='10'>d/f</span><span dataname='1' key='11'>1</span>
      <span dataname=' ' key='12'>break</span>
    </p>
    <div class="sticky-note">as soon as you finish press u,1</div>
  </div>
</li>
<li class="combo-item jin-combo v3.01" id="combo-1000">
  <div class="combo">
    <div class="powered"><div><strong>10 hits</strong> | <strong>90 damages</strong></div></div>
    <p class="comboImg">
      <span dataname='EWGF' key='0'>EWGF</span><span dataname=' ' key='1'>break</span>
      <span dataname='1+2' key='2'>1+2</span>
    </p>
  </div>
</li>
</ul>
"""


def test_parse_extracts_notation():
    combos = parse_combos(FIXTURE, limit=5)
    assert len(combos) == 2
    assert combos[0].notation == "d/f 2 ► W! ► f N d d/f 1"
    assert combos[1].notation == "EWGF ► 1+2"


def test_parse_extracts_damage_and_version():
    combos = parse_combos(FIXTURE, limit=5)
    assert combos[0].damage == "73 damages (7 hits)"
    assert combos[0].source == "kage:v3.02"
    assert combos[0].label == "Kage #2489"


def test_parse_extracts_note():
    combos = parse_combos(FIXTURE, limit=5)
    assert "u,1" in combos[0].note


def test_limit():
    combos = parse_combos(FIXTURE, limit=1)
    assert len(combos) == 1
