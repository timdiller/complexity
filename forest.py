import numpy as np
from numpy.random import uniform
from scipy.ndimage.measurements import label

from chaco.api import ArrayPlotData, Plot, VPlotContainer
from enable.api import ComponentEditor
from encore.events.api import EventManager, HeartbeatEvent, Heartbeat
from traits.api import (HasTraits, Array, Bool, Button, DelegatesTo, Enum,
                        Instance, Int, Property, Range,
                        String)
from traitsui.api import ButtonEditor, HGroup, Item, VGroup, View

history_length = 3000


def randbool(nx, ny, p):
    return uniform(size=(nx, ny)) <= p


class Forest(HasTraits):
    p_lightning = Range(0., 0.0005, 5.e-6)
    p_sapling = Range(0., 0.005, 0.0025)
    forest_trees = Array(dtype=bool)
    forest_fires = Array(dtype=bool)
    size_x = Int(150)
    size_y = Int(150)

    def _forest_trees_default(self):
        return np.zeros((self.size_x, self.size_y))

    def _forest_fires_default(self):
        return np.zeros((self.size_x, self.size_y))

    def advance_one_day(self):
        self.grow_trees()
        self.start_fires()
        self.burn_trees()

    def grow_trees(self):
        growth_sites = randbool(self.size_x, self.size_y, self.p_sapling)
        self.forest_trees[growth_sites] = True

    def burn_trees(self):
        fires = np.zeros((self.size_x + 2, self.size_y + 2), dtype=bool)
        fires[1:-1, 1:-1] = self.forest_fires
        north = fires[:-2, 1:-1]
        south = fires[2:, 1:-1]
        east = fires[1:-1, :-2]
        west = fires[1:-1, 2:]
        new_fires = (north | south | east | west) & self.forest_trees
        self.forest_trees[self.forest_fires] = False
        self.forest_fires = new_fires

    def start_fires(self):
        lightning_strikes = randbool(self.size_x, self.size_y,
                                     self.p_lightning) & self.forest_trees
        self.forest_fires[lightning_strikes] = True


class InstantBurnForest(Forest):

    def advance_one_day(self):
        self.grow_trees()
        self.strike_and_burn()

    def strike_and_burn(self):
        strikes = randbool(self.size_x, self.size_y,
                           self.p_lightning) & self.forest_trees
        groves, num_groves = label(self.forest_trees)
        fires = set(groves[strikes])
        self.forest_fires.fill(False)
        for fire in fires:
            self.forest_fires[groves == fire] = True
        self.forest_trees[self.forest_fires] = False


class ForestView(HasTraits):
    # UI Elements
    day = Button("Advance 1 Day")
    histograms = Instance(Plot)
    fire_time_plot = Instance(Plot)
    forest_plot = Instance(Plot)
    forest_image = Property(Array, depends_on="forest")
    run_label = Property(String, depends_on="run")
    run_button = Button
    time_plots = Instance(VPlotContainer)
    trait_to_histogram = Property(depends_on="which_histogram")
    tree_time_plot = Instance(Plot)
    which_histogram = Enum("trees", "fire")

    # ModelView Elements
    density_function = Property(Array)
    fractions = Property(Array(dtype=float))
    fire_history = Array(dtype=float)
    forest = Instance(Forest)
    p_sapling = DelegatesTo("forest", "p_sapling")
    p_lightning = DelegatesTo("forest", "p_lightning")
    plot_data = Instance(ArrayPlotData)
    time = Array(dtype=int)
    tree_history = Array(dtype=float)

    # Control Elements
    em = Instance(EventManager)
    hb = Instance(Heartbeat)
    run = Bool

    traits_view = View(
        HGroup(
            VGroup(
                VGroup(Item("forest_plot",
                       editor=ComponentEditor(),
                       show_label=False),),
                Item("p_sapling", label="trees"),
                Item("p_lightning", label="fires"),
            ),
            VGroup(
                Item("time_plots", editor=ComponentEditor(),
                     show_label=False),
                HGroup(
                    Item("run_button",
                         editor=ButtonEditor(label_value="run_label"),
                         show_label=False),
                    Item("which_histogram", show_label=False),
                    Item("day", show_label=False),
                ),
            ),
        ),
        resizable=True,
    )

    def hb_listener(self, event):
        self._advance()
        event.mark_as_handled()

    def update_fire_history(self):
        self.fire_history[1:] = self.fire_history[:-1]
        self.fire_history[0] = float(np.sum(self.forest.forest_fires)) / \
            self.forest.forest_fires.size

    def update_tree_history(self):
        self.tree_history[1:] = self.tree_history[:-1]
        self.tree_history[0] = float(np.sum(self.forest.forest_trees)) / \
            self.forest.forest_trees.size

    def update_time(self):
        self.time[1:] = self.time[:-1]
        self.time[0] = self.time[1] + 1

    def _advance(self):
        self.forest.advance_one_day()
        self.update_fire_history()
        self.update_tree_history()
        self.update_time()
        self.plot_data.set_data("forest_image", self.forest_image)
        self.plot_data.set_data("fire_history", self.fire_history)
        self.plot_data.set_data("tree_history", self.tree_history)
        self.plot_data.set_data("density_function",
                                self.density_function)
        self.plot_data.set_data("time", self.time)
        self.plot_data.set_data("fractions", self.fractions)

    def _day_fired(self):
        self._advance()

    def _em_default(self):
        em = EventManager()
        return em

    def _fire_history_default(self):
        return np.zeros((history_length, ), dtype=float)

    def _fire_time_plot_default(self):
        plot = Plot(self.plot_data, title="Fractional area with fires")
        plot.plot(["time", "fire_history"])
        return plot

    def _forest_plot_default(self):
        plot = Plot(self.plot_data)
        plot.img_plot("forest_image")
        plot.bounds = [0., 2.0]
        return plot

    def _get_fractions(self):
        data = self.trait_to_histogram
        return np.linspace(data.min(), data.max(), 50)

    def _get_fire_density_function(self):
        hist, bins = np.histogram(self.fire_history, bins=self.fractions,
                                  normed=True)
        return hist / np.sum(hist)

    def _get_density_function(self):
        time_since_start = self.time > 0
        data = self.trait_to_histogram
        hist, bins = np.histogram(data[time_since_start],
                                  bins=self.fractions, normed=True)
        return hist / np.sum(hist)

    def _get_forest_image(self):
        image = np.zeros((self.forest.size_x, self.forest.size_y, 3),
                         dtype=np.uint8)
        image[:, :, 0] = 255 * self.forest.forest_fires
        image[:, :, 1] = 128 * self.forest.forest_trees
        return image

    def _get_run_label(self):
        if self.run:
            label = "Stop"
        else:
            label = "Run"
        return label

    def _get_trait_to_histogram(self):
        trait_to_histogram = {
            "trees": self.tree_history,
            "fire": self.fire_history,
        }
        return trait_to_histogram[self.which_histogram]

    def _hb_default(self):
        return Heartbeat(interval=0.02, event_manager=self.em)

    def _histograms_default(self):
        plot = Plot(self.plot_data)
        plot.plot(["fractions", "density_function"], color="green")
        return plot

    def _plot_data_default(self):
        data = ArrayPlotData(forest_image=self.forest_image,
                             tree_history=self.tree_history,
                             fire_history=self.fire_history,
                             fractions=self.fractions,
                             density_function=self.density_function,
                             time=self.time)
        return data

    def _run_button_fired(self):
        if self.run:
            self.run = False
        else:
            self.run = True

    def _run_changed(self):
        if self.run:
            self.em.connect(HeartbeatEvent, self.hb_listener)
        else:
            self.em.disconnect(HeartbeatEvent, self.hb_listener)

    def _run_default(self):
        self.hb.serve()
        return False

    def _time_plots_default(self):
        return VPlotContainer(self.fire_time_plot, self.tree_time_plot,
                              self.histograms, spacing=0.)

    def _tree_history_default(self):
        return np.zeros((history_length, ), dtype=float)

    def _tree_time_plot_default(self):
        plot = Plot(self.plot_data, title="Fractional area covered by trees")
        plot.plot(["time", "tree_history"])
        return plot

    def _time_default(self):
        return np.zeros((history_length, ), dtype=int)


if __name__ == "__main__":
    # f = InstantBurnForest()
    f = Forest()
    fv = ForestView(forest=f)
    fv.configure_traits()
