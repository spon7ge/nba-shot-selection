
WITH group_totals AS (
    SELECT season,
           teamTricode AS team,
           shot_group,
           COUNT(*) AS fga,
           SUM(made) AS fgm,
           SUM(three_made) AS fg3m,
           SUM(points) AS points
    FROM shots
    GROUP BY season, teamTricode, shot_group
)
SELECT season, team, shot_group, fga, fgm, fg3m, points,
       1.0 * fgm / fga AS fg_pct,
       1.0 * points / fga AS ppa,
       1.0 * (fgm + 0.5 * fg3m) / fga AS efg_pct,
       1.0 * fga / SUM(fga) OVER (PARTITION BY season, team) AS shot_share
FROM group_totals
ORDER BY season, team, fga DESC


SELECT season, teamTricode AS team,
       COUNT(DISTINCT gameId) AS games, COUNT(*) AS fga,
       SUM(made) AS fgm, SUM(three_made) AS fg3m,
       SUM(points) AS points,
       1.0 * SUM(points) / COUNT(*) AS ppa,
       1.0 * (SUM(made) + 0.5 * SUM(three_made)) / COUNT(*) AS efg_pct
FROM shots
GROUP BY season, teamTricode
ORDER BY season, team
