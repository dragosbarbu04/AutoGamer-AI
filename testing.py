import retro

env = retro.make(game='Airstriker-Genesis')

obs = env.reset()
print(type(obs))
print(obs)
