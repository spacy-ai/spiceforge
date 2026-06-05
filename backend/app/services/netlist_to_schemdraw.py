from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# 1. DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class NetlistElement:
    refdes:  str
    kind:    str
    nodes:   List[str]
    value:   str
    options: Dict[str, str] = field(default_factory=dict)

    @property
    def is_two_terminal(self) -> bool:
        return self.kind in ('R', 'C', 'L', 'D', 'Z', 'SW', 'V', 'I')

    @property
    def is_source(self) -> bool:
        return self.kind in ('V', 'I')

    @property
    def is_multi_terminal(self) -> bool:
        return self.kind in ('Q', 'M', 'OP')


@dataclass
class LayoutBlock:
   
    kind:               str
    entry_net:          str
    exit_net:           str
    elements:           List[NetlistElement]
    par_shunt_indices:  Set[int] = field(default_factory=set)


@dataclass
class Circuit:
    elements:      List[NetlistElement]
    net_els:       Dict[str, List[NetlistElement]]
    net_degree:    Dict[str, int]
    ground_nets:   List[str]
    top_net:       str
    blocks:        List[LayoutBlock]
    device_shunts: Dict[str, List[LayoutBlock]]


# ---------------------------------------------------------------------------
# 2. PARSER  (NGSpice-compatible)
# ---------------------------------------------------------------------------

_KIND_RE     = re.compile(r'^([A-Za-z]+)', re.ASCII)
_GROUND_NETS = {'0', 'gnd', 'agnd', 'dgnd', 'vss', 'ground'}

_PIN_COUNT: Dict[str, int] = {
    'R': 2, 'C': 2, 'L': 2, 'D': 2, 'Z': 2, 'SW': 2, 'V': 2, 'I': 2,
    'Q': 3,
    'M': 3,  
    'OP': 3,
}

_VALUE_STRIP = re.compile(
    r'^(?:DC|AC|PULSE|SIN|EXP|PWL|SFFM)\s*[\(\s]*', re.IGNORECASE
)
_VALUE_TRAIL  = re.compile(r'[\)\s]+$')
_REFDES_RE    = re.compile(r'^[A-Za-z]+\d', re.ASCII)


def _kind(refdes: str) -> str:
    m = _KIND_RE.match(refdes)
    return m.group(1).upper() if m else refdes.upper()


def _is_gnd(n: str) -> bool:
    return n.lower() in _GROUND_NETS


def _clean_value(raw: str) -> str:
    v = _VALUE_STRIP.sub('', raw.strip())
    v = _VALUE_TRAIL.sub('', v)
    return v.strip()


def _looks_like_element(line: str) -> bool:
    return bool(_REFDES_RE.match(line))


def parse_netlist(text: str) -> List[NetlistElement]:
    """
    Parse an NGSpice netlist.

    Title handling: the first non-blank, non-comment line is treated as the
    NGSpice title (ignored) ONLY if it does not look like a component line.
    This preserves netlists that start directly with an element.
    """
    els: List[NetlistElement] = []
    lines = [ln.strip() for ln in text.splitlines()]

    # Optionally consume title line
    for i, ln in enumerate(lines):
        if not ln or ln.startswith(('*', '.', '#')):
            continue
        if not _looks_like_element(ln):
            lines[i] = ''          # blank out the title
        break                      # stop after first substantive line

    for line in lines:
        if not line or line.startswith(('*', '.', '#')):
            continue

        tokens = line.split()
        if len(tokens) < 3:
            continue

        refdes = tokens[0]
        kind   = _kind(refdes)
        nc     = _PIN_COUNT.get(kind, 2)

        if len(tokens) < nc + 1:
            continue

        nodes = tokens[1:1 + nc]

        # Strip model names: tokens after nodes that look like identifiers
        remaining = tokens[1 + nc:]
        val_tokens = [
            tok for tok in remaining
            if not (re.match(r'^[A-Za-z][A-Za-z_]', tok)
                    and not re.match(r'^[0-9]', tok))
        ]
        raw_value = ' '.join(val_tokens)
        value     = _clean_value(raw_value) if raw_value else ''

        els.append(NetlistElement(
            refdes=refdes, kind=kind, nodes=nodes, value=value
        ))

    return els


# ---------------------------------------------------------------------------
# 3. TOPOLOGY ANALYSIS
# ---------------------------------------------------------------------------

def _chain_exit(chain: List[NetlistElement], entry: str) -> str:
    cur = entry
    for el in chain:
        cur = el.nodes[1] if el.nodes[0] == cur else el.nodes[0]
    return cur


def analyse_topology(elements: List[NetlistElement]) -> Circuit:


    # ── All nets ──────────────────────────────────────────────────────────────
    all_nets: List[str] = []
    for el in elements:
        for n in el.nodes:
            if n not in all_nets:
                all_nets.append(n)

    ground_nets = [n for n in all_nets if _is_gnd(n)]

    # ── Source positive terminal ───────────────────────────────────────────────
    sources = [el for el in elements if el.is_source]
    top_net = (
        next((n for n in sources[0].nodes if not _is_gnd(n)), sources[0].nodes[0])
        if sources else (all_nets[0] if all_nets else '')
    )

    # ── Passive-only net index ─────────────────────────────────────────────────
    passive_els = [el for el in elements if el.is_two_terminal and not el.is_source]

    net_els:    Dict[str, List[NetlistElement]] = {n: [] for n in all_nets}
    net_degree: Dict[str, int]                  = {n: 0  for n in all_nets}

    for el in passive_els:
        for n in el.nodes:
            net_els[n].append(el)
            net_degree[n] += 1

    # ── Interior node predicate ────────────────────────────────────────────────
    def _is_interior(n: str) -> bool:
        if _is_gnd(n) or n == top_net:
            return False
        if net_degree.get(n, 0) != 2:
            return False
        return not any(
            _is_gnd(x)
            for el in net_els.get(n, [])
            for x in el.nodes
        )

    # ── Parallel group detection ───────────────────────────────────────────────
    pair_map: Dict[Tuple[str, str], List[NetlistElement]] = {}
    for el in passive_els:
        key = (min(el.nodes[0], el.nodes[1]), max(el.nodes[0], el.nodes[1]))
        pair_map.setdefault(key, []).append(el)

    parallel_groups: List[Tuple[Tuple[str, str], List[NetlistElement]]] = [
        (k, v) for k, v in pair_map.items() if len(v) > 1
    ]
    par_refdes: Set[str] = {el.refdes for _, grp in parallel_groups for el in grp}

    # ── Series chain detection ─────────────────────────────────────────────────
    excluded: Set[str] = set(par_refdes)
    visited:  Set[str] = set(excluded)
    series_chains: List[List[NetlistElement]] = []

    for start_el in passive_els:
        if start_el.refdes in visited:
            continue
        chain = [start_el]
        visited.add(start_el.refdes)

        for direction in (1, 0):           # 1 = forward, 0 = backward
            cur = start_el.nodes[direction]
            while _is_interior(cur):
                cands = [e for e in net_els[cur] if e.refdes not in visited]
                if len(cands) != 1:
                    break
                nxt = cands[0]
                if direction == 1:
                    chain.append(nxt)
                else:
                    chain.insert(0, nxt)
                visited.add(nxt.refdes)
                cur = nxt.nodes[1] if nxt.nodes[0] == cur else nxt.nodes[0]

        series_chains.append(chain)

    # ── Chain classification ───────────────────────────────────────────────────
    def _classify_chain(
        chain: List[NetlistElement],
    ) -> Tuple[str, str, str, List[NetlistElement]]:
        entry = chain[0].nodes[0]
        exit_ = _chain_exit(chain, entry)
        gnd_e, gnd_x = _is_gnd(entry), _is_gnd(exit_)

        if not gnd_e and not gnd_x:
            if net_degree.get(entry, 0) <= net_degree.get(exit_, 0):
                return 'series', entry, exit_, chain
            return 'series', exit_, entry, list(reversed(chain))

        if gnd_e and gnd_x:
            return 'skip', entry, exit_, chain

        sig     = exit_ if gnd_e else entry
        ordered = list(reversed(chain)) if gnd_e else chain
        if _chain_exit(ordered, sig) == sig:
            ordered = list(reversed(ordered))

        other_els = [
            e for e in net_els.get(sig, [])
            if e.refdes not in {x.refdes for x in chain}
        ]

        if sig != top_net or other_els:
            return 'shunt', sig, sig, ordered

        gnd_n = _chain_exit(ordered, sig)
        return 'series', sig, gnd_n, ordered

    # ── Device-pin shunt detection ─────────────────────────────────────────────
    # A passive is a device-pin shunt when:
    #   - One terminal is ground
    #   - The signal-side net is exclusively a multi-terminal device pin
    #     (no other passives share that net)
    device_pin_refdes: Set[str] = set()
    device_shunt_map:  Dict[str, List[LayoutBlock]] = {}

    for el in passive_els:
        if len(el.nodes) < 2:
            continue
        n0, n1   = el.nodes[0], el.nodes[1]
        gnd0, gnd1 = _is_gnd(n0), _is_gnd(n1)
        if not (gnd0 ^ gnd1):
            continue

        sig_net = n1 if gnd0 else n0
        other_passives = [
            e for e in net_els.get(sig_net, []) if e.refdes != el.refdes
        ]
        if other_passives:
            continue

        owning: Optional[str] = None
        for dev in elements:
            if dev.is_multi_terminal and sig_net in dev.nodes:
                owning = dev.refdes
                break

        if owning is None:
            continue

        device_pin_refdes.add(el.refdes)
        device_shunt_map.setdefault(owning, []).append(
            LayoutBlock('shunt', sig_net, sig_net, [el])
        )

    device_shunts: Dict[str, List[LayoutBlock]] = device_shunt_map

    # ── Pre-compute shunts keyed by their signal net ───────────────────────────
    # Used to merge exit-net shunts into parallel blocks.
    # Each shunt: signal_net → LayoutBlock
    pre_shunts: Dict[str, List[LayoutBlock]] = {}

    for chain in series_chains:
        if any(e.refdes in device_pin_refdes for e in chain):
            continue
        kind, entry, exit_, ordered = _classify_chain(chain)
        if kind == 'shunt':
            pre_shunts.setdefault(entry, []).append(
                LayoutBlock('shunt', entry, entry, ordered)
            )

    # Shunts from parallel groups with one gnd terminal
    for (n0, n1), grp in parallel_groups:
        if _is_gnd(n0) or _is_gnd(n1):
            sig = n1 if _is_gnd(n0) else n0
            pre_shunts.setdefault(sig, []).append(
                LayoutBlock('shunt', sig, sig, list(grp))
            )

    # ── Build block index ──────────────────────────────────────────────────────
    net_to_blocks: Dict[str, List[LayoutBlock]] = {n: [] for n in all_nets}
    shunts_at:     Dict[str, List[LayoutBlock]] = {n: [] for n in all_nets}

    registered_refdes: Set[str] = set()

    def _register(blk: LayoutBlock) -> None:
        refs = {e.refdes for e in blk.elements}
        if refs & registered_refdes:
            return
        registered_refdes.update(refs)
        if blk.kind == 'shunt':
            shunts_at[blk.entry_net].append(blk)
        else:
            net_to_blocks[blk.entry_net].append(blk)
            if not _is_gnd(blk.exit_net):
                rev = LayoutBlock(
                    blk.kind, blk.exit_net, blk.entry_net,
                    list(reversed(blk.elements))
                )
                net_to_blocks[blk.exit_net].append(rev)

    # Register parallel groups, merging exit-net shunts as extra branches
    for (n0, n1), grp in parallel_groups:
        if _is_gnd(n0) or _is_gnd(n1):
            # Handled in pre_shunts above
            continue

        # Determine which net is the exit (further from top_net)
        # The entry is whichever of n0/n1 is top_net or closer to it.
        if n0 == top_net or n1 == top_net:
            entry_net = top_net
            exit_net  = n1 if n0 == top_net else n0
        else:
            entry_net = n0
            exit_net  = n1

        all_elements     = list(grp)
        shunt_indices:   Set[int] = set()

        # Merge shunts whose signal-net == exit_net into this parallel block
        # as extra branches (they go down from top rail and need Ground() at bottom)
        merged_shunt_refdes: Set[str] = set()
        for sblk in pre_shunts.get(exit_net, []):
            for el in sblk.elements:
                idx = len(all_elements)
                all_elements.append(el)
                shunt_indices.add(idx)
                merged_shunt_refdes.add(el.refdes)

        blk = LayoutBlock(
            kind='parallel',
            entry_net=entry_net,
            exit_net=exit_net,
            elements=all_elements,
            par_shunt_indices=shunt_indices,
        )
        _register(blk)

        # Mark merged shunts as registered so BFS won't re-place them
        registered_refdes.update(merged_shunt_refdes)

    # Register series/shunt chains
    for chain in series_chains:
        if any(e.refdes in device_pin_refdes for e in chain):
            continue
        kind, entry, exit_, ordered = _classify_chain(chain)
        if kind == 'skip':
            continue
        _register(LayoutBlock(kind, entry, exit_, ordered))

    # Multi-terminal device blocks
    mt_blocks: List[LayoutBlock] = []
    for el in elements:
        if el.kind == 'Q':
            mt_blocks.append(LayoutBlock('bjt',    el.nodes[2], el.nodes[0], [el]))
        elif el.kind == 'M':
            mt_blocks.append(LayoutBlock('mosfet', el.nodes[2], el.nodes[0], [el]))
        elif el.kind == 'OP':
            mt_blocks.append(LayoutBlock('opamp',  el.nodes[0], el.nodes[2], [el]))

    # ── BFS from top_net ───────────────────────────────────────────────────────
    placed_refdes: Set[str] = set()   # grows as BFS actually places blocks
    placed_blocks: List[LayoutBlock] = []
    net_queue: deque[str] = deque([top_net])
    net_seen:  Set[str]   = {top_net}

    def _place_shunts(net: str) -> None:
        for sblk in shunts_at.get(net, []):
            refs = {e.refdes for e in sblk.elements}
            if refs & placed_refdes:
                continue
            placed_blocks.append(sblk)
            placed_refdes.update(refs)

    _place_shunts(top_net)

    while net_queue:
        cur = net_queue.popleft()
        for blk in net_to_blocks.get(cur, []):
            refs = {e.refdes for e in blk.elements}
            if refs & placed_refdes:
                continue
            placed_blocks.append(blk)
            placed_refdes.update(refs)
            nxt = blk.exit_net
            if nxt not in net_seen and not _is_gnd(nxt):
                net_seen.add(nxt)
                net_queue.append(nxt)
            _place_shunts(nxt)

    # Remaining passives the BFS could not reach
    for el in passive_els:
        if el.refdes in placed_refdes or el.refdes in device_pin_refdes or el.refdes in registered_refdes:
            continue
        kind, entry, exit_, ordered = _classify_chain([el])
        if kind == 'skip':
            continue
        placed_blocks.append(LayoutBlock(kind, entry, exit_, ordered))
        placed_refdes.add(el.refdes)

    # Append multi-terminal devices, each immediately followed by device-pin shunts
    for mt_blk in mt_blocks:
        placed_blocks.append(mt_blk)
        dev_ref = mt_blk.elements[0].refdes
        for shunt_blk in device_shunts.get(dev_ref, []):
            placed_blocks.append(shunt_blk)

    return Circuit(
        elements=elements,
        net_els=net_els,
        net_degree=net_degree,
        ground_nets=ground_nets,
        top_net=top_net,
        blocks=placed_blocks,
        device_shunts=device_shunts,
    )


# ---------------------------------------------------------------------------
# 4. DRAW HELPERS
# ---------------------------------------------------------------------------

def _label(refdes: str, value: str) -> str:
    return f"'{refdes}\\n{value}'" if value else f"'{refdes}'"


_DRAW_TMPL: Dict[str, str] = {
    'R':  "elm.Resistor().{dir}().label({lbl})",
    'C':  "elm.Capacitor().{dir}().label({lbl})",
    'L':  "elm.Inductor2().{dir}().label({lbl})",
    'D':  "elm.Diode().{dir}().label({lbl})",
    'Z':  "elm.Zener().{dir}().label({lbl})",
    'SW': "elm.Switch().{dir}().label({lbl})",
}


def _draw(el: NetlistElement, direction: str = 'right') -> str:
    tmpl = _DRAW_TMPL.get(el.kind)
    if tmpl:
        return tmpl.format(dir=direction, lbl=_label(el.refdes, el.value))
    return f"# UNSUPPORTED {el.refdes}"




def emit_code(circuit: Circuit, unit: int = 3) -> str:
    hdr = [
        "import schemdraw",
        "import schemdraw.elements as elm",
        "",
        f"UNIT = {unit}",
        "",
        "with schemdraw.Drawing() as d:",
        "    d.config(unit=UNIT)",
        "",
    ]

    body:           List[str] = []
    sources         = [el for el in circuit.elements if el.is_source]
    first_src_var:  Optional[str] = None
    on_ground_rail: bool = False
    par_idx:        int  = 0

    # ── Sources ────────────────────────────────────────────────────────────────
    for src in sources:
        var = src.refdes.lower()
        if first_src_var is None:
            first_src_var = var
        kexpr = "elm.SourceV()" if src.kind == 'V' else "elm.SourceI()"
        body.append(
            f"{var} = d.add({kexpr}.up().label({_label(src.refdes, src.value)}))"
        )

    if sources:
        body.append(
            f"d.add(elm.Line().right(UNIT).at({sources[-1].refdes.lower()}.end))"
        )
        body.append("")

    # ── Blocks ─────────────────────────────────────────────────────────────────
    for blk in circuit.blocks:

        # ── Series ─────────────────────────────────────────────────────────────
        if blk.kind == 'series':
            if on_ground_rail:
                body.append("# Raise to top rail")
                body.append("d.add(elm.Line().up(UNIT))")
                on_ground_rail = False
                body.append("")
            body.append(f"# Series: {' — '.join(e.refdes for e in blk.elements)}")
            for el in blk.elements:
                body.append(f"d.add({_draw(el, 'right')})")
            body.append("")

        # ── Parallel ───────────────────────────────────────────────────────────
        elif blk.kind == 'parallel':
            n   = len(blk.elements)
            pfx = f"_p{par_idx}"
            par_idx += 1

            body.append(
                f"# Parallel ({n} branches): "
                f"{', '.join(e.refdes for e in blk.elements)}"
            )
            # Save top-left anchor
            body.append(f"{pfx}_tl = d.here")
            # Top rail spans all N columns
            body.append(f"d.add(elm.Line().right({n} * UNIT))")
            body.append("")

            # Each branch drawn .down() from its column on the top rail
            for i, el in enumerate(blk.elements):
                x_off = i * unit
                body.append(f"# branch {i}: {el.refdes}")
                body.append(
                    f"d.add({_draw(el, 'down')}"
                    f".at(({pfx}_tl[0] + {x_off}, {pfx}_tl[1])))"
                )
                # Merged-shunt branches need an explicit Ground() at their bottom
                if i in blk.par_shunt_indices:
                    body.append(
                        f"d.add(elm.Ground()"
                        f".at(({pfx}_tl[0] + {x_off}, {pfx}_tl[1] - UNIT)))"
                    )
                body.append("")

            # Bottom rail spans all N columns (including merged-shunt columns)
            body.append(
                f"d.add(elm.Line().right({n} * UNIT)"
                f".at(({pfx}_tl[0], {pfx}_tl[1] - UNIT)))"
            )
            body.append(f"{pfx}_br = d.here")
            body.append(f"d.here = {pfx}_br")
            body.append("")
            on_ground_rail = True

        # ── Shunt ──────────────────────────────────────────────────────────────
        elif blk.kind == 'shunt':
            body.append(
                f"# Shunt→GND: {', '.join(e.refdes for e in blk.elements)}"
            )
            body.append("_shunt_top = d.here")
            for el in blk.elements:
                body.append(f"d.add({_draw(el, 'down')})")
            body.append("d.add(elm.Ground())")
            body.append("d.here = _shunt_top")
            body.append("")

        # ── BJT ────────────────────────────────────────────────────────────────
        elif blk.kind == 'bjt':
            el  = blk.elements[0]
            var = el.refdes.lower()
            body.append(
                f"# BJT {el.refdes}  C={el.nodes[0]} B={el.nodes[1]} E={el.nodes[2]}"
            )
            body.append(
                f"{var} = d.add(elm.BjtNpn(circle=True)"
                f".label('{el.refdes}', loc='right'))"
            )
            body.append("")

        # ── MOSFET ─────────────────────────────────────────────────────────────
        elif blk.kind == 'mosfet':
            el  = blk.elements[0]
            var = el.refdes.lower()
            body.append(
                f"# MOSFET {el.refdes}  D={el.nodes[0]} G={el.nodes[1]} S={el.nodes[2]}"
            )
            body.append(
                f"{var} = d.add(elm.NFet()"
                f".label('{el.refdes}', loc='right'))"
            )
            body.append("")

        # ── Op-amp ─────────────────────────────────────────────────────────────
        elif blk.kind == 'opamp':
            el  = blk.elements[0]
            var = el.refdes.lower()
            body.append(f"# Opamp {el.refdes}")
            body.append(
                f"{var} = d.add(elm.Opamp(leads=True)"
                f".label('{el.refdes}', loc='center', ofst=0))"
            )
            body.append(
                f"d.add(elm.Line().right({max(1, unit // 4)}).at({var}.out))"
            )
            body.append("")

    if first_src_var:
        body.append("# Close loop")
        if not on_ground_rail:
            body.append("d.add(elm.Line().down(UNIT))")
        body.append(f"d.add(elm.Line().tox({first_src_var}.start))")
        body.append("d.add(elm.Ground())")

    return '\n'.join(hdr + ["    " + ln for ln in body])



def netlist_to_schemdraw(netlist_text: str, unit: int = 3) -> str:
 
    elements = parse_netlist(netlist_text)
    circuit  = analyse_topology(elements)
    return emit_code(circuit, unit=unit)


def render_schemdraw_svg(code: str, out_path: str) -> str:

    import schemdraw
    import schemdraw.elements as elm
    from pathlib import Path

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    exec_code = code.replace(
        "with schemdraw.Drawing() as d:",
        f"with schemdraw.Drawing(file={str(out)!r}, show=False) as d:",
        1,
    )
    exec(exec_code, {"schemdraw": schemdraw, "elm": elm}, {})
    return str(out)