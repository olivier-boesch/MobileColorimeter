"""
Colorimetry

Support classes for colorimetry and absorbance analysis

Olivier Boesch (c) 2023
"""
from math import log10
from numpy.polynomial import polynomial as poly
import logging

log = logging.getLogger("Colorimetry")
log.setLevel(logging.DEBUG)


class Sample:
    def __init__(self, red_value: int = 0, green_value: int = 0, blue_value: int = 0,
                 concentration: float = 0, reference: "Sample" = None) -> None:
        """
        Sample for colorimetry
        red_value : red component (0 to 255)
        green_value : green compnent (0 to 255)
        blue_value : blue compnent (0 to 255)
        concentration : concentration of sample in mol/L
        reference: other Sample object used as background (or None if not provided)
        """
        self.red_value = red_value
        self.green_value = green_value
        self.blue_value = blue_value
        self.concentration = concentration
        self.reference = reference
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
    def transmittance(self) -> float:
        """
        computes and returns the transmittance for this sample (value from 0.0 to 1.0)
        """
        if self.reference is None:
            raise ValueError("Must provide a reference to compute transmittance of sample")
        sample_intensity = self.intensity
        reference_intensity = self.reference.intensity
        transmittance_value = sample_intensity / reference_intensity
        log.debug(f"computed Transmittance: {transmittance_value * 100:.2f}%")
        return transmittance_value

    @property
    def absorbance(self) -> float:
        """
        computes and returns abdorbance for this sample in arbritrary units (A.U.)
        """
        absorbance_value = - log10(self.transmittance)
        log.debug(f"computed absorbance: {absorbance_value}")
        return absorbance_value


class Session:
    def __init__(self) -> None:
        self.samples: list[Sample] = []
        self._reference: Sample | None = None

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
    def reference(self) -> Sample:
        """
        returns the reference (background) Sample object
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
        self.samples.append(sample)

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
    def absorbance_data_points(self) -> list[tuple[float, float]]:
        """
        computes list of data points (concentration, absorbance) for plotting purpose
        """
        sorted_samples = sorted(self.samples, key=lambda o: o.concentration)
        return [(s.concentration, s.absorbance) for s in sorted_samples]

    @property
    def absorbance_data_line(self) -> tuple[list[float], float]:
        """
        computes the regression line A = a * C + b for plotting purpose
        C is the concentration in mol/L
        r2 is the residual R²
        return object : ([b, a], r2)
        """
        coefs, stats = poly.polyfit(x=[s.concentration for s in self.samples],
                                    y=[s.absorbance for s in self.samples],
                                    deg=[1], full=True)
        # TODO: problème avec R² (non toujours renvoyé)
        r2 = stats[0][0]
        return coefs, r2

    def compute_concentration_from_absorbance(self, absorbance: float) -> float:
        """
        computes the predicted concentration from given absorbance and the session data samples
        """
        coeffs = poly.polyfit(y=[s.concentration for s in self.samples],
                              x=[s.absorbance for s in self.samples],
                              deg=[1])
        return coeffs[0] + coeffs[1] * absorbance

    def to_file(self, filename: str) -> None:
        """
        saves session informations to file
        """
        with open(filename, mode='w', encoding="utf8") as f:
            f.write(str(self))


def test_sample():
    from math import isclose, log10
    s = Sample(red_value=0, green_value=60, blue_value=120, concentration=1.0)
    assert isclose(s.intensity, 60)
    ref = Sample(red_value=100, green_value=100, blue_value=150, concentration=0.0)
    s.reference = ref
    assert isclose(s.transmittance, s.intensity / ref.intensity)
    assert isclose(s.absorbance, - log10(s.intensity / ref.intensity))
    print(s.absorbance, s.transmittance, s.intensity, ref.intensity, s, ref)


def test_session():
    session = Session()
    s = Sample(red_value=0, green_value=60, blue_value=120, concentration=1.0)
    session.add_sample(s)
    s = Sample(red_value=0, green_value=60, blue_value=120, concentration=1.0)
    session.add_sample(s)
    ref = Sample(red_value=100, green_value=100, blue_value=150, concentration=0.0)
    session.reference = ref
    print(session)
    print(session.compute_concentration_from_absorbance(0.56))


if __name__ == '__main__':
    test_sample()
    test_session()
