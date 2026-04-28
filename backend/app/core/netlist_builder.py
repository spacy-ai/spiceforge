from __future__ import annotations

from typing import Optional


class CircuitBuilder:
    def __init__(self, title: str = "SPICY Circuit"):
        self._title = title
        self._global_node = "0"
        self._models: list[str] = []
        self._components: list[str] = []
        self._analyses: list[str] = []
        self._comments: list[str] = []

    def title(self, title: str) -> "CircuitBuilder":
        self._title = title
        return self

    def comment(self, text: str) -> "CircuitBuilder":
        self._comments.append(f"* {text}")
        return self

    def global_node(self, node: str) -> "CircuitBuilder":
        self._global_node = node
        return self

    def model(self, name: str, model_type: str, **params) -> "CircuitBuilder":
        param_str = " ".join(f"{k}={v}" for k, v in params.items())
        self._models.append(f".model {name} {model_type} {param_str}")
        return self

    def resistor(self, name: str, n1: str, n2: str, value: str) -> "CircuitBuilder":
        self._components.append(f"R{name} {n1} {n2} {value}")
        return self

    def capacitor(self, name: str, n1: str, n2: str, value: str) -> "CircuitBuilder":
        self._components.append(f"C{name} {n1} {n2} {value}")
        return self

    def inductor(self, name: str, n1: str, n2: str, value: str) -> "CircuitBuilder":
        self._components.append(f"L{name} {n1} {n2} {value}")
        return self

    def voltage_source(
        self,
        name: str,
        n1: str,
        n2: str,
        dc: Optional[float] = None,
        ac: Optional[float] = None,
        pulse: Optional[dict] = None,
        sine: Optional[dict] = None,
        pwl: Optional[list] = None,
    ) -> "CircuitBuilder":
        parts = [f"V{name}", n1, n2]

        if pulse:
            v1 = pulse.get("v1", 0)
            v2 = pulse.get("v2", 1)
            td = pulse.get("td", 0)
            tr = pulse.get("tr", 1e-9)
            tf = pulse.get("tf", 1e-9)
            pw = pulse.get("pw", 1e-3)
            per = pulse.get("per", 2e-3)
            parts.append(f"PULSE({v1} {v2} {td} {tr} {tf} {pw} {per})")
        elif sine:
            vo = sine.get("vo", 0)
            va = sine.get("va", 1)
            freq = sine.get("freq", 1e3)
            td = sine.get("td", 0)
            phi = sine.get("phi", 0)
            parts.append(f"SINE({vo} {va} {freq} {td} {phi})")
        elif pwl:
            pwl_str = " ".join(f"{t},{v}" for t, v in pwl)
            parts.append(f"PWL({pwl_str})")
        else:
            if dc is not None:
                parts.append(f"DC {dc}")
            if ac is not None:
                parts.append(f"AC {ac}")

        self._components.append(" ".join(parts))
        return self

    def current_source(
        self,
        name: str,
        n1: str,
        n2: str,
        dc: Optional[float] = None,
        ac: Optional[float] = None,
    ) -> "CircuitBuilder":
        parts = [f"I{name}", n1, n2]
        if dc is not None:
            parts.append(f"DC {dc}")
        if ac is not None:
            parts.append(f"AC {ac}")
        self._components.append(" ".join(parts))
        return self

    def diode(self, name: str, n1: str, n2: str, model: str) -> "CircuitBuilder":
        self._components.append(f"D{name} {n1} {n2} {model}")
        return self

    def mosfet(
        self,
        name: str,
        nd: str,
        ng: str,
        ns: str,
        nb: str,
        model: str,
        w: Optional[float] = None,
        l: Optional[float] = None,
    ) -> "CircuitBuilder":
        parts = [f"M{name}", nd, ng, ns, nb, model]
        if w is not None:
            parts.append(f"W={w}")
        if l is not None:
            parts.append(f"L={l}")
        self._components.append(" ".join(parts))
        return self

    def bjt(
        self,
        name: str,
        nc: str,
        nb: str,
        ne: str,
        model: str,
        area: Optional[float] = None,
    ) -> "CircuitBuilder":
        parts = [f"Q{name}", nc, nb, ne, model]
        if area is not None:
            parts.append(f"AREA={area}")
        self._components.append(" ".join(parts))
        return self

    def opamp(self, name: str, nout: str, ninv: str, nnoninv: str) -> "CircuitBuilder":
        self._components.append(f"U{name} {nout} {ninv} {nnoninv} 0 0 OP07")
        return self

    def subcircuit(
        self, name: str, nodes: list[str], subckt_name: str
    ) -> "CircuitBuilder":
        nodes_str = " ".join(nodes)
        self._components.append(f"X{name} {nodes_str} {subckt_name}")
        return self

    def transformer(
        self,
        name: str,
        n1: str,
        n2: str,
        n3: str,
        n4: str,
        ratio: float,
    ) -> "CircuitBuilder":
        self._components.append(f"K{name} {n1} {n2} {n3} {n4} {ratio}")
        return self

    def transmission_line(
        self,
        name: str,
        n1a: str,
        n1b: str,
        n2a: str,
        n2b: str,
        z0: float,
        td: Optional[float] = None,
        f: Optional[float] = None,
    ) -> "CircuitBuilder":
        parts = [f"T{name}", n1a, n1b, n2a, n2b]
        if td is not None:
            parts.append(f"TD={td}")
        elif f is not None:
            parts.append(f"F={f}")
        parts.append(f"Z0={z0}")
        self._components.append(" ".join(parts))
        return self

    def voltage_controlled_switch(
        self,
        name: str,
        n1: str,
        n2: str,
        nc1: str,
        nc2: str,
        model: str,
    ) -> "CircuitBuilder":
        self._components.append(f"S{name} {n1} {n2} {nc1} {nc2} {model}")
        return self

    def ac_analysis(
        self,
        start_freq: float,
        stop_freq: float,
        num_points: int = 100,
        sweep_type: str = "dec",
    ) -> "CircuitBuilder":
        self._analyses.append(f".ac {sweep_type} {num_points} {start_freq} {stop_freq}")
        return self

    def dc_sweep(
        self,
        source: str,
        start: float,
        stop: float,
        increment: float,
    ) -> "CircuitBuilder":
        self._analyses.append(f".dc {source} {start} {stop} {increment}")
        return self

    def transient(
        self,
        tstart: float,
        tstop: float,
        tstep: float,
        tmax: Optional[float] = None,
    ) -> "CircuitBuilder":
        if tmax:
            self._analyses.append(f".tran {tstep} {tstop} {tstart} {tmax}")
        else:
            self._analyses.append(f".tran {tstep} {tstop} {tstart}")
        return self

    def operating_point(self) -> "CircuitBuilder":
        self._analyses.append(".op")
        return self

    def noise(
        self,
        output: str,
        input_source: str,
        points: int = 100,
        start_freq: float = 1,
        stop_freq: float = 1e9,
    ) -> "CircuitBuilder":
        self._analyses.append(
            f".noise {output} {input_source} dec {points} {start_freq} {stop_freq}"
        )
        return self

    def netlist(self) -> str:
        lines = []
        lines.append(f"* {(self._title or '').strip()}")

        for comment in self._comments:
            lines.append(comment)

        if self._global_node != "0":
            lines.append(f".global {self._global_node}")

        for model in self._models:
            lines.append(model)

        lines.extend(self._components)

        if self._analyses:
            lines.append("")
            for analysis in self._analyses:
                lines.append(analysis)

        lines.append(".end")

        netlist = "\n".join(lines)
        while "\n\n\n" in netlist:
            netlist = netlist.replace("\n\n\n", "\n\n")
        return netlist.rstrip() + "\n"
