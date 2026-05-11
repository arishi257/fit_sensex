from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from fit_sensex.config import AppConfig
from fit_sensex.market.instruments import OptionChain
from fit_sensex.market.kite_stream import MarketDataStore
from fit_sensex.models import AnalyticsResult
from fit_sensex.pricing.vol_curve import ParametricVolCurve
from fit_sensex.services.analytics import AnalyticsEngine


class FitSensexApp:
    def __init__(
        self,
        root: tk.Tk,
        config: AppConfig,
        chain: OptionChain,
        store: MarketDataStore,
        analytics: AnalyticsEngine,
    ) -> None:
        self.root = root
        self.config = config
        self.chain = chain
        self.store = store
        self.analytics = analytics

        self.root.title("Dynamic Synthetic Futures + IV Parametric Fit")
        self._build_ui()

    def start(self) -> None:
        self.refresh()
        self.root.mainloop()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        table_tab = tk.Frame(notebook)
        plot_tab = tk.Frame(notebook)
        iv_plot_tab = tk.Frame(notebook)
        error_tab = tk.Frame(notebook)
        cash_vol_tab = tk.Frame(notebook)

        notebook.add(table_tab, text="Option Chain")
        notebook.add(plot_tab, text="Slope Plot")
        notebook.add(iv_plot_tab, text="IV Smile")
        notebook.add(error_tab, text="IV Error")
        notebook.add(cash_vol_tab, text="Cash Vol Curve")

        top_tables_frame = tk.Frame(table_tab)
        top_tables_frame.pack(fill="x", pady=10)
        self.user_tree, self.user_items = self._build_summary_table(
            top_tables_frame,
            "User Inputs",
            [
                "Funding Rate",
                "Brokerage Rate",
                "Low Strike",
                "High Strike",
                "Strike Gap",
                "User Value",
                "Time",
                "Full Days",
                "Fraction Days",
                "Intraday",
                "Intraday Var",
            ],
            side="left",
            padx=10,
        )
        self.market_tree, self.market_items = self._build_summary_table(
            top_tables_frame,
            "Market Variables",
            [
                "Best Synthetic Bid",
                "Best Synthetic Ask",
                "Universal Synthetic Mid",
                "Universal Spot",
                "ATM Vol",
                "Param a",
                "Param bL",
                "Param bR",
                "Param CapL",
                "Param FloorR",
                "Fit Error",
            ],
            side="left",
            padx=30,
        )

        self.tree = ttk.Treeview(
            table_tab,
            columns=["Strike", "Norm Strike", "IV Mid", "Slope"],
            show="headings",
        )
        for col in ["Strike", "Norm Strike", "IV Mid", "Slope"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.strike_to_item = {}
        for strike in sorted(self.chain.keys()):
            item = self.tree.insert("", "end", values=[strike, "", "", ""])
            self.strike_to_item[strike] = item

        self.fig, self.ax, self.canvas = self._build_plot(plot_tab)
        self.iv_fig, self.iv_ax, self.iv_canvas = self._build_plot(iv_plot_tab)
        self.error_fig, self.error_ax, self.error_canvas = self._build_plot(error_tab)
        self.cash_vol_fig, self.cash_vol_ax, self.cash_vol_canvas = self._build_plot(
            cash_vol_tab
        )

    @staticmethod
    def _build_summary_table(parent, title, parameters, side, padx):
        frame = tk.Frame(parent)
        frame.pack(side=side, padx=padx)
        tk.Label(frame, text=title, font=("Arial", 11, "bold")).pack()

        tree = ttk.Treeview(
            frame,
            columns=["Parameter", "Value"],
            show="headings",
            height=12,
        )
        for col in ["Parameter", "Value"]:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")
        tree.pack()

        items = {}
        for name in parameters:
            items[name] = tree.insert("", "end", values=[name, ""])
        return tree, items

    @staticmethod
    def _build_plot(parent):
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return fig, ax, canvas

    def refresh(self) -> None:
        result = self.analytics.calculate(self.store.snapshot())
        if result is not None:
            self._render(result)

        self.root.after(self.config.market.refresh_ms, self.refresh)

    def _render(self, result: AnalyticsResult) -> None:
        self._render_rows(result)
        self._render_summary(result)
        self._render_slope_plot(result)
        self._render_iv_smile(result)
        self._render_error_plot(result)
        self._render_cash_vol_curve(result)

    def _render_rows(self, result: AnalyticsResult) -> None:
        for row in result.rows:
            self.tree.item(
                self.strike_to_item[row.strike],
                values=(
                    row.strike,
                    row.normalized_strike,
                    row.iv_mid,
                    row.slope,
                ),
            )

    def _render_summary(self, result: AnalyticsResult) -> None:
        market = self.config.market
        strikes = self.config.strikes
        a_fit, bl_fit, br_fit, capl_fit, floorr_fit = result.fitted_params

        self._set_user("Funding Rate", f"{round(market.funding_rate * 100, 4)}%")
        self._set_user("Brokerage Rate", f"{round(market.brokerage_rate * 100, 4)}%")
        self._set_user("Low Strike", strikes.low)
        self._set_user("High Strike", strikes.high)
        self._set_user("Strike Gap", strikes.gap)
        self._set_user("User Value", result.user_value)
        self._set_user("Time", f"{round(result.time * 100, 4)}%")
        self._set_user("Full Days", result.full_days)
        self._set_user("Fraction Days", round(result.fraction_days, 4))
        self._set_user("Intraday", round(result.intraday, 4))
        self._set_user("Intraday Var", result.intraday_var)

        self._set_market("Best Synthetic Bid", round(result.best_bid, 2))
        self._set_market("Best Synthetic Ask", round(result.best_ask, 2))
        self._set_market("Universal Synthetic Mid", round(result.universal_mid, 2))
        self._set_market("Universal Spot", round(result.universal_spot, 2))
        self._set_market("ATM Vol", round(result.atm_vol * 100, 2))
        self._set_market("Param a", f"{round(a_fit, 4)}%")
        self._set_market("Param bL", f"{round(bl_fit, 4)}%")
        self._set_market("Param bR", f"{round(br_fit, 4)}%")
        self._set_market("Param CapL", f"{round(capl_fit, 4)}%")
        self._set_market("Param FloorR", f"{round(floorr_fit, 4)}%")
        self._set_market("Fit Error", round(result.fit_error, 4))

    def _set_user(self, name: str, value) -> None:
        self.user_tree.item(self.user_items[name], values=[name, value])

    def _set_market(self, name: str, value) -> None:
        self.market_tree.item(self.market_items[name], values=[name, value])

    def _render_slope_plot(self, result: AnalyticsResult) -> None:
        a_fit, bl_fit, br_fit, capl_fit, floorr_fit = result.fitted_params
        self.ax.clear()
        self.ax.plot(result.slope_x, result.slope_y, marker="o", label="Market Slope")

        model_slope_x = sorted(result.market_ns)
        model_slope_y = [
            ParametricVolCurve.model_slope(
                x, a_fit, bl_fit, br_fit, capl_fit, floorr_fit
            )
            for x in model_slope_x
        ]
        self.ax.plot(model_slope_x, model_slope_y, marker="x", label="Model Slope")
        self.ax.set_xlabel("Normalized Strike")
        self.ax.set_ylabel("Slope")
        self.ax.set_title("Slope vs Normalized Strike")
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

    def _render_iv_smile(self, result: AnalyticsResult) -> None:
        self.iv_ax.clear()
        self.iv_ax.plot(result.market_ns, result.market_iv, marker="o", label="Market IV")
        if len(result.model_vols) == len(result.market_ns):
            self.iv_ax.plot(
                result.market_ns,
                result.model_vols,
                marker="x",
                label="Model IV",
            )
        self.iv_ax.set_xlabel("Normalized Strike")
        self.iv_ax.set_ylabel("IV")
        self.iv_ax.set_title("IV Smile")
        self.iv_ax.grid(True)
        self.iv_ax.legend()
        self.iv_canvas.draw()

    def _render_error_plot(self, result: AnalyticsResult) -> None:
        self.error_ax.clear()
        if result.model_errors and result.market_ns:
            self.error_ax.plot(result.market_ns, result.model_errors, marker="o")
        self.error_ax.axhline(y=0, linestyle="--")
        self.error_ax.set_xlabel("Normalized Strike")
        self.error_ax.set_ylabel("Market IV - Model IV")
        self.error_ax.set_title("IV Error vs Normalized Strike")
        self.error_ax.grid(True)
        self.error_canvas.draw()

    def _render_cash_vol_curve(self, result: AnalyticsResult) -> None:
        plot_rows = [
            row
            for row in sorted(result.rows, key=lambda item: item.strike)
            if row.iv_bid != "" and row.iv_ask != ""
        ]

        strikes = [row.strike for row in plot_rows]
        bid_iv = [float(row.iv_bid) for row in plot_rows]
        ask_iv = [float(row.iv_ask) for row in plot_rows]
        mid_iv = [(bid + ask) / 2 for bid, ask in zip(bid_iv, ask_iv)]
        lower_error = [mid - bid for mid, bid in zip(mid_iv, bid_iv)]
        upper_error = [ask - mid for ask, mid in zip(ask_iv, mid_iv)]
        model_rows = [row for row in plot_rows if row.model_iv is not None]
        model_strikes = [row.strike for row in model_rows]
        model_iv = [float(row.model_iv) for row in model_rows]

        self.cash_vol_ax.clear()
        if strikes:
            self.cash_vol_ax.errorbar(
                strikes,
                mid_iv,
                yerr=[lower_error, upper_error],
                fmt="none",
                color="#0f9d80",
                ecolor="#0f9d80",
                elinewidth=1.3,
                capsize=3,
                markersize=4,
                label="Market Bid/Ask IV",
            )
        if model_strikes:
            self.cash_vol_ax.plot(
                model_strikes,
                model_iv,
                color="#9c00c8",
                linewidth=1.8,
                label="Fitted Vol Curve",
            )

        self.cash_vol_ax.set_xlabel("Cash Strike")
        self.cash_vol_ax.set_ylabel("IV")
        self.cash_vol_ax.set_title("Fitted Vol Curve vs Market Bid/Ask IV")
        self.cash_vol_ax.grid(True)
        self.cash_vol_ax.legend()
        self.cash_vol_canvas.draw()
