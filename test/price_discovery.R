library(mvtnorm)
l = c(30, 40, 70, 40, 20)
u = c(50, 80, 100, 80, 60)

true.prices = array(0, dim = length(l))
for (i in 1:length(l)) {
  true.prices[i] = runif(1, l[i], u[i])
}

q = sample(c(0.5, 0.7, 1.3, 3.5), replace = F)

R = matrix(
  c(1, -0.6437, 0.09173, -0.2531, 0.6453,
    -0.6437,1,-0.6588,0.5011, -0.1258,
    0.09173, -0.6588, 1, -0.1996, -0.17288,
    -0.2531, 0.5011, -0.1996, 1, -0.3718,
    0.6453, -0.1258, -0.17288, -0.3718, 1),
  byrow = T, 5, 5)

preds = vector(mode = "list", length = length(1:10))
for (t in 1:10) {
  s = sample(1:4, 1)
  preds[[t]] = list(
    news.source = s,
    pred = rmvnorm(1, as.vector(true.prices), q[s]^2 * R * (600 - t) / 60)
    )
} 

f = function(theta, preds, n) {
  sum = 0
  q.bar = theta[1:4]
  p.bar = theta[5:9]
  for (i in 1:length(p.bar)) {
    sum = sum + dunif(p.bar[i], l[i], u[i], log = T)
  }
  for (i in 1:length(q.bar)) {
    sum = sum + dunif(q.bar[i], log(min(q)), log(max(q)), log = T)
  }
  for (t in 1:n) {
    sum = sum + log(dmvnorm(preds[[t]]$pred, p.bar, exp(q.bar[preds[[t]]$news.source])^2 * R * (600 - t) / 60))
  }
  sum
}

preds = vector(mode = "list", length = length(1:4))
preds[[1]] = list(news.source = 1, pred = c(33.68, 63.54,87.12,54.12,18.58)) 
preds[[2]] = list(news.source = 2, pred = c(37.57,64.72,88.28,55.84,18.03))
preds[[3]] = list(news.source = 2, pred = c(37.37, 63.66,88.73,53.76,16.82))
preds[[4]] = list(news.source = 2, pred = c(37.57,64.72,88.28,55.84,30.03))
# preds[[4]] = list(news.source = , pred = c())
# preds[[5]] = list(news.source = , pred = c())
# preds[[6]] = list(news.source = , pred = c())
# preds[[7]] = list(news.source = , pred = c())
# preds[[8]] = list(news.source = , pred = c())
# preds[[9]] = list(news.source = , pred = c())
# preds[[10]] = list(news.source = , pred = c())
mh.draws <- mcmc(start = c(rep(log(mean(q)), 4), (l + u) /2),
             iterations = 3000,
             burn = 1000,
             type = "mh",
             trace = 500,
             d.posterior = function(proposal) { f(proposal, preds, 1)},
             r.proposal = function(n, mean) { rmvnorm(1, mean, adiag(diag(rep(0.02, 4)), diag(0.5, 5))) }
)