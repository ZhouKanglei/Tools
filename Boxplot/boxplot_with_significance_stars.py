import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.rcParams['savefig.bbox'] = 'tight'

import numpy as np
import seaborn as sns
from scipy import stats
import os

def boxplot_with_significance_stars(data, title, ylabel, xticklabels, figname='boxplot_with_significance_stars.pdf'):
    """
    Create a box-and-whisker plot with significance bars.
    """
    ax = plt.axes()
    mean = {"marker": 'o', 'markerfacecolor': 'white', 'markeredgecolor': 'gray', 'markersize': 6, "color": 'gray'}

    bp = ax.boxplot(data, widths=0.6, patch_artist=True, meanprops=mean, meanline=True, showmeans=True)
    # Graph title
    ax.set_title(title, fontsize=14)
    # Label y-axis
    ax.set_ylabel(ylabel)
    # Label x-axis ticks
    ax.set_xticklabels(xticklabels)
    # Hide x-axis major ticks
    ax.tick_params(axis='x', which='major', length=0)
    # Show x-axis minor ticks
    xticks = [0.5] + [x + 0.5 for x in ax.get_xticks()]
    ax.set_xticks(xticks, minor=True)
    # Clean up the appearance
    ax.tick_params(axis='x', which='minor', length=3, width=1)

    # Change the colour of the boxes to Seaborn's 'pastel' palette
    colors = sns.color_palette('pastel')
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    # Colour of the median lines
    plt.setp(bp['medians'], color='k')

    # Check for statistical significance
    significant_combinations = []
    # Check from the outside pairs of boxes inwards
    ls = list(range(1, len(data) + 1))
    combinations = [(ls[x], ls[x + y]) for y in reversed(ls) for x in range((len(ls) - y))]
    for c in combinations:
        data1 = data[c[0] - 1]
        data2 = data[c[1] - 1]
        # Significance
        U, p = stats.mannwhitneyu(data1, data2, alternative='two-sided')
        if p < 0.05:
            significant_combinations.append([c, p])

    # Get info about y-axis
    bottom, top = ax.get_ylim()
    yrange = top - bottom

    # Significance bars
    for i, significant_combination in enumerate(significant_combinations):
        # Columns corresponding to the datasets of interest
        x1 = significant_combination[0][0]
        x2 = significant_combination[0][1]
        # What level is this bar among the bars above the plot?
        level = len(significant_combinations) - i
        # Plot the bar
        bar_height = (yrange * 0.08 * level) + top
        bar_tips = bar_height - (yrange * 0.02)
        plt.plot(
            [x1, x1, x2, x2],
            [bar_tips, bar_height, bar_height, bar_tips], lw=1, c='gray')
        # Significance level
        p = significant_combination[1]
        if p < 0.001:
            sig_symbol = '***'
        elif p < 0.01:
            sig_symbol = '**'
        elif p < 0.05:
            sig_symbol = '*'
        text_height = bar_height + (yrange * 0.01)
        plt.text((x1 + x2) * 0.5, text_height, sig_symbol, ha='center', c='k')

    # Adjust y-axis
    bottom, top = ax.get_ylim()
    yrange = top - bottom
    ax.set_ylim(bottom - 0.02 * yrange, top)
    ax.set_ylim(bottom, top)

    # Annotate sample size below each box
    # for i, dataset in enumerate(data):
    #     sample_size = len(dataset)
    #     ax.text(i + 1, bottom, fr'n = {sample_size}', ha='center', size='x-small')

    # plt.show()
    plt.savefig(figname)
    if 'pdf' in figname:
        os.system(f'pdfcrop {figname} {figname}')

if __name__ == '__main__':
    data = []
    for x in range(4):
        mu = 650 + 100 * x
        sigma = 50 + 20 * x
        n = 30 + np.random.randint(0, 100)
        data.append(np.random.normal(mu, sigma, n))
    title = 'Random Data - Four Groups'
    ylabel = r'Measurement, $m$ / units'
    xticklabels = ['First Group', 'Second Group', 'Third Group', 'Fourth Group']
    boxplot_with_significance_stars(data, title, ylabel, xticklabels, figname='boxplot_with_significance_stars.png')