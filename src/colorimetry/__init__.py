"""
Colorimetry

Support classes for colorimetry and absorbance analysis

Olivier Boesch (c) 2023
"""
from math import log10
from numpy.polynomial import polynomial as poly
import logging
from os.path import join, expanduser
from os import remove
from kivy.base import platform

log = logging.getLogger("Colorimetry")
log.setLevel(logging.INFO)


class Sample:
    def __init__(self, red_value: int = 0, green_value: int = 0, blue_value: int = 0,
                 concentration: float = 0, reference: ["Sample", None] = None) -> None:
        """
        Sample for colorimetric analysis
        ---
        red_value : red component (0 to 255)
        green_value : green component (0 to 255)
        blue_value : blue component (0 to 255)
        concentration : concentration of sample in mol/L
        reference: other Sample object used as background (or None if not provided)
        """
        self.red_value: int = red_value
        self.green_value: int = green_value
        self.blue_value: int = blue_value
        self.concentration: float = concentration
        self.reference: [Sample, None] = reference
        log.debug(f"Sample added -> {self}")

    def __str__(self):
        return f"Sample: RGB: {str(self.values)}, C: {self.concentration:.2e} mol/L, I: {self.intensity:.2e} A.U."

    __repr__ = __str__

    @property
    def values(self) -> tuple[int, int, int]:
        """
        returns a rgb tuple of sample components
        """
        return self.red_value, self.green_value, self.blue_value

    @property
    def intensity(self) -> float:
        """
        computes and returns the intensity of the sample
        the model of human vision is NOT used
        """
        intensity = sum(self.values) / 3
        log.debug(f"computed intensity: {intensity}")
        return intensity

    @property
    def transmittance(self) -> [float, None]:
        """
        computes and returns the transmittance for this sample (value from 0.0 to 1.0)
        """
        if self.reference is None:
            return None
        transmittance_value = self.intensity / self.reference.intensity
        log.debug(f"computed Transmittance: {transmittance_value * 100:.2f}%")
        return transmittance_value

    @property
    def absorbance(self) -> [float, None]:
        """
        computes and returns abdorbance for this sample in arbritrary units (A.U.)
        """
        if self.transmittance is None:
            return None
        absorbance_value = - log10(self.transmittance)
        log.debug(f"computed absorbance: {absorbance_value}")
        return absorbance_value


class Session:
    def __init__(self) -> None:
        """
        Session for colorimetric analysis
        ---
        manages samples and updates reference
        evaluates regressions expressions for concentration and absorbance
        Export reports for analysis in pdf format
        """
        self.samples: list[Sample] = []
        self._reference: Sample | None = None
        self.max_concentration = 0.0

    def __str__(self):
        coefs, r2 = self.absorbance_data_line
        output = "------- Session ---------\n"
        output += f"Session of {len(self.samples)} samples\n"
        output += f"regression model: A = {coefs[1]:.5e} * C; R2 = {r2:.5f}\n"
        output += f"Background : {str(self.reference)}"
        output += "------ Samples ------\n"
        for i in range(len(self.samples)):
            output += f"{i}-> {str(self.samples[i])}"
            output += f", A: {self.samples[i].absorbance:.3e} A.U., T:{self.samples[i].transmittance * 100:.2f}%\n"
        output += "--------------------"
        return output

    @property
    def reference(self) -> [Sample, None]:
        """
        returns the reference (background) Sample object or None if not set
        """
        return self._reference

    @reference.setter
    def reference(self, new_val: Sample | None) -> None:
        """
        sets the reference (background) Sample object
        also set the reference for all already stored samples
        call with None to remove the reference Sample Object
        """
        self._reference = new_val
        for i in range(len(self.samples)):
            self.samples[i].reference = new_val

    def add_sample(self, sample: Sample) -> None:
        """
        stores a new sample and sets the reference sample with the one of the session
        """
        sample.reference = self._reference
        if sample.concentration > self.max_concentration:
            self.max_concentration = sample.concentration
        self.samples.append(sample)
        self.samples.sort(key=lambda s: s.concentration)

    def clear_samples(self) -> None:
        """
        deletes all the samples
        """
        self.samples.clear()

    def remove_sample(self, index_or_sample: Sample | int) -> None:
        """
        remove a sample by its index or reference
        """
        if isinstance(index_or_sample, int):
            del self.samples[index_or_sample]
        elif isinstance(index_or_sample, Sample):
            self.samples.remove(index_or_sample)
        else:
            raise TypeError("parameter must be an int or Sample object")

    @property
    def maximum_concentration(self) -> float:
        return self.max_concentration

    @property
    def absorbance_data_points(self) -> list[tuple[float, float, "Sample"]]:
        """
        computes list of data points (concentration, absorbance) for plotting purpose
        """
        return [(s.concentration, s.absorbance, s) for s in self.samples]

    @property
    def absorbance_data_line(self) -> tuple[float, float, float]:
        """
        computes the regression line A = a * C for plotting purpose
        C is the concentration in mol/L
        r2 is the residual R²
        return object : (a, r2)
        r2 is None if it can't be computed
        """
        coefs, stats = poly.polyfit(x=[s.concentration for s in self.samples],
                                    y=[s.absorbance for s in self.samples],
                                    deg=[1,0], full=True)
        try:
            r2 = 1-stats[0][0]
        except IndexError:
            r2 = None
        log.info(f"data line regression: A={coefs[1]} * C + {coefs[0]}")
        return coefs[0], coefs[1], r2

    def compute_concentration_from_sample(self, sample: Sample) -> float:
        """
        computes the predicted concentration from given absorbance and the session data samples
        """
        sample.reference = self.reference
        coeffs = poly.polyfit(y=[s.concentration for s in self.samples],
                              x=[s.absorbance for s in self.samples],
                              deg=[0,1])
        concentration = float(coeffs[1] * sample.absorbance + coefs[0])
        log.debug(f"computed concentration: {concentration}")
        return concentration

    def export_report(self, number: int):
        """
        Exports data analysis as a pdf report
        :param number: number of analysis
        :return: None
        """
        from reportlab.lib import pagesizes, styles, units, utils
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
        import matplotlib
        matplotlib.use('agg')
        from matplotlib import pyplot as plt
        # storage dir
        if platform == 'android':
            from androidstorage4kivy import SharedStorage
            from androidstorage4kivy.sharedstorage import Environment
            ss = SharedStorage()

            storage_dir = "."

            def store_file(filepath):
                ss.copy_to_shared(filepath, Environment.DIRECTORY_DOCUMENTS)
                remove(filepath)  # cleanup

        else:
            def store_file(filepath):
                pass

            storage_dir = join(expanduser("~"), "Documents")

        # document
        path = join(storage_dir, f"report{number}.pdf")
        log.info(f"Pdf report: saving file to {path}")
        doc = SimpleDocTemplate(path, pagesize=pagesizes.A4)
        elements = []
        # title
        p = Paragraph(f"Analyse par colormétrie (session n°{number})", style=styles.ParagraphStyle(name="title", font="Arial", fontSize=25, align="center"))
        elements.append(p)
        # space
        elements.append(Spacer(height=1 * units.cm, width=pagesizes.A4[0]))
        # table of data
        data = [["C (mol/L)", "R", "G", "B", "I (U.A.)", "T (%)", "A (U.A.)"]]
        plot_data_x = []  # for future graph
        plot_data_y = []  # for future graph
        for s in self.samples:
            data.append([f"{s.concentration:.3e}", f"{s.red_value:d}", f"{s.green_value:d}", f"{s.blue_value:d}", f"{s.intensity:.3f}", f"{s.transmittance*100:.2f}", f"{s.absorbance:.3f}"])
            plot_data_x.append(s.concentration)
            plot_data_y.append(s.absorbance)
        t = Table(data=data, style=TableStyle(name="samples", font="Arial", fontSize=10, align="center"))
        elements.append(t)
        # space
        elements.append(Spacer(height=1 * units.cm, width=pagesizes.A4[0]))
        # equation
        b, a, r2 = self.absorbance_data_line
        text = f"Equation : A = {a:.3e} C + {b:.3e}"
        if r2 is not None:
            text += f", R² = {r2:.5f}"
        p = Paragraph(text=text, style=styles.ParagraphStyle(name="body", font="Arial", fontSize=12, align="center", bold=True))
        elements.append(p)
        # space
        elements.append(Spacer(height=1 * units.cm, width=pagesizes.A4[0]))
        # graph
        plt.figure(0, dpi=600)
        plt.scatter(plot_data_x, plot_data_y, s=20, color='black')
        plt.plot([0, self.max_concentration], [b, self.max_concentration * a + b], color='#212121', linestyle='--')
        plt.xlabel("Concentration (mol/L)")
        plt.ylabel("Absorbance")
        plt.grid(True)
        plt.savefig("temp.png", dpi=600)
        img = utils.ImageReader("temp.png")
        iw, ih = img.getSize()
        aspect = ih / iw
        elements.append(Image("temp.png", width=15*units.cm, height=15*aspect*units.cm))
        # build and save document
        doc.build(elements)
        log.info("Pdf report: file saved")
        # store file (used for android)
        store_file(path)
        # cleanup
        remove('temp.png')

