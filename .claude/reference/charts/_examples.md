<!-- last-reviewed: 2026-05-18 -->

# Chart pattern gallery

Approved patterns for common chart needs. Use as a starting point; deviate
only with a reason. Edit `last-reviewed` when re-verifying.

## Time series of a single metric

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
ax.plot(df["date"], df["value"], color="#0072B2", linewidth=1.5)
ax.set_title("Revenue grew 12% YoY")
ax.set_xlabel("Date")
ax.set_ylabel("Revenue (USD)")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/revenue-yoy.png")
```

## Distribution comparison across categories

```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
sns.boxplot(data=df, x="group", y="value", order=df.groupby("group")["value"].median().sort_values().index, palette="colorblind", ax=ax)
ax.set_title("Group B has the widest spread")
fig.tight_layout()
fig.savefig("figures/value-by-group.png")
```

## Ranked categorical

Use horizontal bar; sort descending; annotate the top.

```python
top = df.groupby("category")["count"].sum().nlargest(10).sort_values()
fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
ax.barh(top.index, top.values, color="#0072B2")
ax.set_title("Top 10 categories")
fig.tight_layout()
fig.savefig("figures/top-10-categories.png")
```

## Two numeric variables

Scatter for <5k points; hexbin or 2D-histogram for larger.

```python
fig, ax = plt.subplots(figsize=(7, 7), dpi=150)
ax.scatter(df["x"], df["y"], alpha=0.4, s=10, color="#0072B2")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("y vs x")
fig.tight_layout()
fig.savefig("figures/y-vs-x.png")
```

## Multi-series (small multiples)

Prefer faceting (`plt.subplots`) over color-overlay when series > 3.

```python
fig, axes = plt.subplots(2, 2, figsize=(10, 8), dpi=150, sharex=True, sharey=True)
for ax, (name, group) in zip(axes.flat, df.groupby("series")):
    ax.plot(group["t"], group["v"], color="#0072B2")
    ax.set_title(name)
fig.suptitle("Series comparison")
fig.tight_layout()
fig.savefig("figures/series-facet.png")
```
